"""Exact aggregation over a qualified relationship graph and disjoint data sets."""

from fractions import Fraction
import re
from decimal import Context, Decimal, localcontext
from .kern import _umschlag

_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}\Z")
_NAT = re.compile(r"(?:0|[1-9][0-9]{0,255})\Z")
_DEC = re.compile(r"(?:0|[1-9][0-9]*)(?:\.[0-9]+)?\Z")


def aggregiere_unternehmensgruppe(
    stamm_id,
    unternehmen,
    beziehungen,
    datenkreise,
    *,
    groesse,
    bezugsperiode,
    kreis_vollstaendig,
    quellenfassung,
):
    """Aggregate qualified linked components and their direct partner components.

    Does not classify legal relationships, establish consolidated accounts, or
    decide SME/SMC status. See UNTERNEHMENSGRUPPEN.md for the disjoint-data contract.
    """
    inputs = dict(
        stamm_id=stamm_id,
        unternehmen=unternehmen,
        beziehungen=beziehungen,
        datenkreise=datenkreise,
        groesse=groesse,
        bezugsperiode=bezugsperiode,
        kreis_vollstaendig=kreis_vollstaendig,
    )
    out = _umschlag("UNTERNEHMENSGRUPPE_AGGREGATION", inputs, quellenfassung)
    out.update(regelversion="0.1.0", ergebnistyp="OBJEKT")
    missing = set()

    def fail(message):
        raise ValueError(message)

    def identity(x):
        return isinstance(x, str) and _ID.fullmatch(x) is not None

    def array(x, label):
        if not isinstance(x, list) or len(x) > 10000:
            fail(label + ": Liste mit hoechstens10000Eintraegen erforderlich")

    def decimal(x):
        if not isinstance(x, str) or len(x) > 256 or not _DEC.fullmatch(x):
            fail(
                "Nichtnegativer exakter Dezimaltext mit hoechstens256Zeichen erforderlich"
            )
        return Fraction(x)

    def value(x):
        if x is None:
            return None
        if groesse != "JAE":
            return decimal(x)
        if not isinstance(x, dict) or set(x) != {"zaehler", "nenner"}:
            fail("JAE verlangt zaehler/nenner als Ganzzahltexte")
        if (
            any(not isinstance(v, str) or not _NAT.fullmatch(v) for v in x.values())
            or x["nenner"] == "0"
        ):
            fail("Ungueltiger JAE-Bruch")
        return Fraction(int(x["zaehler"]), int(x["nenner"]))

    def show(x):
        if groesse == "JAE":
            return dict(zaehler=str(x.numerator), nenner=str(x.denominator))
        # All financial inputs and weights are finite decimals. Exact finite
        # division needs at most digits(numerator)+digits(denominator)+16 places.
        with localcontext(
            Context(prec=len(str(x.numerator)) + len(str(x.denominator)) + 16)
        ):
            text = format(Decimal(x.numerator) / Decimal(x.denominator), "f")
        return text.rstrip("0").rstrip(".") if "." in text else text

    def ratio(x):
        return dict(zaehler=str(x.numerator), nenner=str(x.denominator))

    try:
        if quellenfassung != "EUAIACT_2026_07_27":
            fail("Quellenfassung fuer diese Regel nicht verfuegbar")
        if (
            not identity(stamm_id)
            or not identity(bezugsperiode)
            or groesse not in ("JAE", "UMSATZ_EUR", "BILANZ_EUR")
        ):
            fail("Stamm-ID, Bezugsperiode oder Groesse ungueltig")
        if kreis_vollstaendig is not None and type(kreis_vollstaendig) is not bool:
            fail("kreis_vollstaendig verlangt Boolean oder null")
        for x, label in (
            (unternehmen, "unternehmen"),
            (beziehungen, "beziehungen"),
            (datenkreise, "datenkreise"),
        ):
            array(x, label)
        if (
            not unternehmen
            or any(not identity(x) for x in unternehmen)
            or len(set(unternehmen)) != len(unternehmen)
            or stamm_id not in unternehmen
        ):
            fail("Unternehmens-IDs muessen eindeutig sein und Stamm-ID enthalten")
        parent = {x: x for x in unternehmen}

        def root(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        partners = []
        for edge in beziehungen:
            if not isinstance(edge, dict) or edge.get("art") not in (
                "VERBUND",
                "PARTNER",
            ):
                fail("Ungueltige qualifizierte Beziehung")
            expected = {"von", "nach", "art"} | (
                {"quote"} if edge["art"] == "PARTNER" else set()
            )
            if (
                set(edge) != expected
                or not identity(edge.get("von"))
                or not identity(edge.get("nach"))
                or edge.get("von") not in parent
                or edge.get("nach") not in parent
                or edge["von"] == edge["nach"]
            ):
                fail("Beziehungsfelder oder Unternehmensverweise ungueltig")
            if edge["art"] == "VERBUND":
                a, b = root(edge["von"]), root(edge["nach"])
                parent[max(a, b)] = min(a, b)
            else:
                q = decimal(edge["quote"])
                if not Fraction(1, 4) <= q <= 1:
                    fail("Qualifizierte Partnerquote muss zwischen0.25und1 liegen")
                partners.append((edge["von"], edge["nach"], q))
        components = {x: root(x) for x in unternehmen}
        own = components[stamm_id]
        weights = {g: Fraction(0) for g in components.values()}
        weights[own] = Fraction(1)
        seen_pairs = set()
        for a, b, q in partners:
            a, b = components[a], components[b]
            pair = tuple(sorted((a, b)))
            if a == b or pair in seen_pairs:
                fail(
                    "Partnerbeziehung innerhalb Verbund oder mehrfach zwischen Verbundgruppen; Gruppenquote zuvor eindeutig qualifizieren"
                )
            seen_pairs.add(pair)
            if a == own:
                weights[b] = q
            elif b == own:
                weights[a] = q
        # No traversal from a partner component to its own partner components.
        coverage, person_segments, circles = set(), set(), set()
        total = Fraction(0)
        details = []
        for record in sorted(
            datenkreise,
            key=lambda x: x.get("kreis_id", "")
            if isinstance(x, dict) and isinstance(x.get("kreis_id"), str)
            else "",
        ):
            keys = {"kreis_id", "unternehmen_ids", "wert"} | (
                {"personensegmente"} if groesse == "JAE" else set()
            )
            if (
                not isinstance(record, dict)
                or set(record) != keys
                or not identity(record["kreis_id"])
                or record["kreis_id"] in circles
            ):
                fail("Datenkreisfelder oder eindeutige Kreis-ID ungueltig")
            circles.add(record["kreis_id"])
            ids = record["unternehmen_ids"]
            array(ids, "unternehmen_ids")
            if (
                not ids
                or any(not isinstance(x, str) or x not in parent for x in ids)
                or len(set(ids)) != len(ids)
                or coverage.intersection(ids)
            ):
                fail(
                    "Datenkreise ueberlappen oder enthalten ungueltige Unternehmens-IDs"
                )
            coverage.update(ids)
            ws = {weights[components[x]] for x in ids}
            if len(ws) != 1:
                fail(
                    "Gemischte Hinzurechnungsquoten in einem Datenkreis; qualifizierte disjunkte Aufteilung erforderlich"
                )
            w = ws.pop()
            v = value(record["wert"])
            if groesse == "JAE":
                array(record["personensegmente"], "personensegmente")
                for segment in record["personensegmente"]:
                    if (
                        not isinstance(segment, dict)
                        or set(segment) != {"person_id", "segment_id"}
                        or not all(identity(x) for x in segment.values())
                    ):
                        fail("Ungueltige Personen-/Segmentidentitaet")
                    pair = (segment["person_id"], segment["segment_id"])
                    if pair in person_segments:
                        fail(
                            "Personensegment mehrfach erfasst; keine doppelte Personalhinzurechnung"
                        )
                    person_segments.add(pair)
                if v is not None and v > 0 and not record["personensegmente"]:
                    fail(
                        "Positive JAE erfordern ein identifiziertes qualifiziertes Personensegmentinventar"
                    )
            if w > 0 and v is None:
                missing.add("datenkreise." + record["kreis_id"] + ".wert")
            contribution = None if v is None else v * w
            if contribution is not None:
                total += contribution
                if total.numerator >= 10**4096 or total.denominator >= 10**4096:
                    fail(
                        "Zwischenergebnis ueberschreitet4096Ziffern; Datenkreis fachlich aufteilen"
                    )
            details.append(
                dict(
                    operation="DATENKREIS_GEWICHTEN",
                    kreis_id=record["kreis_id"],
                    unternehmen_ids=sorted(ids),
                    gewicht=ratio(w),
                    beruecksichtigt=w > 0,
                    beitrag=show(contribution)
                    if contribution is not None
                    else (show(Fraction(0)) if w == 0 else None),
                )
            )
        for x in sorted(parent):
            if weights[components[x]] > 0 and x not in coverage:
                missing.add("datenkreis_fuer." + x)
        if kreis_vollstaendig is not True:
            missing.add("kreis_vollstaendig")
        out.update(
            status="EINGABE_FEHLT" if missing else "AUSGEWERTET",
            anwendbarkeit="UNBEKANNT",
            entscheidungsstatus="UNBESTIMMT" if missing else "ENTSCHIEDEN",
            einheit=groesse,
            wert=None if missing else dict(summe=show(total)),
            fehlende_angaben=sorted(missing),
            entscheidungsrelevante_luecken=sorted(missing),
            entscheidungsschritte=[
                dict(
                    operation="VERBUND_UND_PARTNERGEWICHT",
                    unternehmen_id=x,
                    verbund_id=components[x],
                    gewicht=ratio(weights[components[x]]),
                )
                for x in sorted(parent)
            ],
            rechenschritte=details,
            annahmen=[
                "Beziehungstypen, gruppenbezogene Partnerquoten, Perioden-/Einheitenbasis und disjunkte konsolidierte Datenkreise vorgelagert qualifiziert"
            ],
            hinweise=[
                "Keine automatische Beziehungseinstufung, Konsolidierungsbuchung oder KMU-/SMC-Statusentscheidung; F008/F014 und Investorenausnahmen separat",
                "Personensegment-IDs identifizieren bereits qualifizierte disjunkte Arbeitsanteile; unterschiedliche Arbeitsverhaeltnisse nicht anhand des Personennamens zusammenfassen",
            ],
            nachweise=[
                dict(art="RECHTSQUELLE", fundstelle=x, quellenfassung=quellenfassung)
                for x in ("32003H0361/ANH/ART_6", "32025H1099/ANH/6")
            ],
        )
    except (ValueError, TypeError) as exc:
        out["hinweise"] = [str(exc)]
    return out
