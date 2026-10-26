"""Exakte gesetzliche Obergrenzen und Hilfsrechnungen mit getrenntem Umfang."""

from copy import deepcopy
from decimal import Context, Decimal, localcontext

from .kern import _fehler, _katalog, _umschlag, _normalisierte_ganzzahlen
from .zeitpunkte import _kalenderdatum, _zeitpunktteile
from .rationale import _rational
from .widerruf import _widerruf_wirksamkeit


def _dezimaltext(wert):
    text = format(wert, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return "0" if Decimal(text) == 0 else text


def _anteil(betrag, satz):
    with localcontext(Context(prec=len(betrag) + len(satz) + 16)):
        return _dezimaltext(Decimal(betrag) * Decimal(satz))


def berechne_regel(regel_id, eingaben, *, quellenfassung):
    """Berechnet ausschließlich die spezifizierte Größe, keine Rechtsanwendbarkeit.

    Fehlende entscheidungsrelevante Daten liefern EINGABE_FEHLT. Geldbeträge
    werden exakt als Dezimaltexte ausgegeben. Es erfolgt keine Cent-Rundung.
    Feste Dauern liefern Anzahl und Einheit bei leerem Eingabeobjekt. Zeitbezug
    und Richtung stehen in regel_info; ein Enddatum wird nicht bestimmt.
    Zeitpunktregeln vergleichen explizite Offset-Zeitstempel ohne Systemzeitzone.
    """
    ergebnis = _umschlag(regel_id, eingaben, quellenfassung)
    if (
        not isinstance(regel_id, str)
        or regel_id not in _katalog()
        or "ausdruck" in _katalog()[regel_id]
    ):
        ergebnis["hinweise"] = ["Unbekannte Rechenregel-ID"]
        return ergebnis
    regel = _katalog()[regel_id]
    ergebnis.update(
        regelversion=regel["regelversion"],
        ergebnistyp=regel.get("ergebnistyp", "OBJEKT"),
        einheit=regel.get("einheit"),
    )
    if quellenfassung != regel["quellenfassung"]:
        ergebnis["hinweise"] = ["Quellenfassung für diese Regel nicht verfügbar"]
        return ergebnis
    fehler = _fehler(eingaben, regel["eingaben"])
    if fehler:
        ergebnis["hinweise"] = fehler
        return ergebnis
    eingaben = _normalisierte_ganzzahlen(eingaben, regel["eingaben"])
    ergebnis["eingaben"] = deepcopy(eingaben)
    fehlend = {name for name in regel["eingaben"] if eingaben.get(name) is None}
    relevant = set(fehlend)
    if (
        regel_id == "AIA_099_OBERGRENZE"
        and eingaben.get("akteurklasse") == "KEIN_UNTERNEHMEN"
    ):
        relevant.discard("weltweiter_vorjahresumsatz_eur")
    if (
        regel.get("operation") == "WIDERRUF_WIRKSAMKEIT"
        and eingaben.get("widerruf_spaeterer_tag_festgelegt") is False
    ):
        relevant.discard("widerruf_festgelegter_tag")
    wert = None
    schritte = []
    if not relevant:
        if regel.get("operation") == "FESTE_DAUER":
            wert = dict(regel["dauer"])
            schritte = [{"operation": "FESTE_DAUER", "wert": wert.copy()}]
        elif regel.get("operation") in (
            "MONATSBRUCH_30_TAGE",
            "RATIONALE_ADDITION",
            "RATIONALE_MULTIPLIKATION",
        ):
            try:
                wert = _rational(regel, eingaben)
            except ValueError as exc:
                ergebnis["hinweise"] = [str(exc)]
                return ergebnis
            schritte = [
                {
                    "operation": regel["operation"],
                    "wert": wert.copy(),
                    "rundung": "KEINE",
                }
            ]
        elif regel.get("operation") == "WIDERRUF_WIRKSAMKEIT":
            try:
                wert = _widerruf_wirksamkeit(eingaben)
            except ValueError as exc:
                ergebnis["hinweise"] = [str(exc)]
                return ergebnis
            schritte = [
                {
                    "operation": "WIDERRUF_WIRKSAMKEIT",
                    "wert": wert.copy(),
                    "endverschiebung": "KEINE",
                }
            ]
        elif regel.get("operation") == "FESTER_PROZENTANTEIL":
            betrag = eingaben[regel["betragsfeld"]]
            wert = _anteil(betrag, regel["satz"])
            schritte = [
                {
                    "operation": "FESTER_PROZENTANTEIL",
                    "operanden": [betrag, regel["satz"]],
                    "wert": wert,
                    "rundung": "KEINE",
                }
            ]
        elif regel.get("operation") == "WIEDERKEHRENDER_KALENDERTERMIN":
            index = eingaben["evaluationszyklus_index"]
            first = regel["erster_termin"]
            years = regel["zyklus_jahre"]
            year = int(first[:4]) + years * index
            wert = f"{year:04d}" + first[4:]
            schritte = [
                dict(
                    operation=regel["operation"],
                    erster_termin=first,
                    zyklus_jahre=years,
                    zyklus_index=index,
                    wert=wert,
                    endverschiebung="KEINE",
                )
            ]
        elif regel.get("operation") == "DATUM_KLEINER_GLEICH_FEST":
            links = eingaben[regel["datumsfeld"]]
            rechts = regel["vergleichsdatum"]
            wert = _kalenderdatum(links) <= _kalenderdatum(rechts)
            schritte = [
                {
                    "operation": regel["operation"],
                    "operanden": [links, rechts],
                    "vergleichsbasis": "Gregorianische Kalenderdaten, einschliessliche Grenze",
                    "wert": wert,
                }
            ]
        elif regel.get("operation") in (
            "ZEITPUNKT_KLEINER_GLEICH",
            "ZEITPUNKT_KLEINER",
        ):
            links = eingaben[regel["frueher"]]
            rechts = eingaben[regel["spaeter"]]
            a, b = _zeitpunktteile(links), _zeitpunktteile(rechts)
            wert = a < b if regel["operation"] == "ZEITPUNKT_KLEINER" else a <= b
            schritte = [
                {
                    "operation": regel["operation"],
                    "operanden": [links, rechts],
                    "vergleichsbasis": "UTC, Mikrosekunden exakt",
                    "wert": wert,
                }
            ]
        elif regel.get("operation") == "EXAKTE_DEZIMALVERKNUEPFUNG":
            a, b = (eingaben[regel[k]] for k in ("links", "rechts"))
            with localcontext(Context(prec=len(a) + len(b) + 16)):
                wert = _dezimaltext(
                    Decimal(a) * Decimal(b)
                    if regel["verknuepfung"] == "MULTIPLIKATION"
                    else Decimal(a) + Decimal(b)
                )
            schritte = [
                {"operation": regel["verknuepfung"], "operanden": [a, b], "wert": wert}
            ]
        elif regel.get("operation") == "GEWICHTETE_HINZURECHNUNG":
            basis = eingaben["aggregationsbasiswert"]
            zusatz = eingaben["noch_hinzuzurechnender_unternehmenswert"]
            quote = (
                eingaben["hinzurechnungsquote"]
                if regel.get("quotenfeld")
                else regel["feste_quote"]
            )
            anteil = _anteil(zusatz, quote)
            with localcontext(Context(prec=len(basis) + len(anteil) + 16)):
                wert = _dezimaltext(Decimal(basis) + Decimal(anteil))
            schritte = [
                {
                    "operation": "MULTIPLIKATION",
                    "operanden": [zusatz, quote],
                    "wert": anteil,
                },
                {"operation": "ADDITION", "operanden": [basis, anteil], "wert": wert},
            ]
        elif regel.get("operation") == "NICHTNEGATIVE_GANZZAHL_DIFFERENZ":
            minuend = eingaben[regel["minuend"]]
            subtrahend = eingaben[regel["subtrahend"]]
            if subtrahend > minuend:
                ergebnis["hinweise"] = [
                    "Ausgenommene Anhangseiten uebersteigen die Gesamtseiten"
                ]
                return ergebnis
            wert = minuend - subtrahend
            schritte = [
                {
                    "operation": "SUBTRAKTION",
                    "operanden": [minuend, subtrahend],
                    "wert": wert,
                }
            ]
        elif regel.get("operation") == "DAUERAUSWAHL":
            feld = regel["auswahlfeld"]
            auswahl = eingaben[feld]
            wert = dict(regel["dauerparameter"][auswahl])
            schritte = [
                {
                    "operation": "DAUERAUSWAHL",
                    "auswahlfeld": feld,
                    "auswahl": auswahl,
                    "wert": wert.copy(),
                }
            ]
        elif regel_id in {"AIA_099_OBERGRENZE", "AIA_101_OBERGRENZE"}:
            if regel_id == "AIA_101_OBERGRENZE":
                festbetrag, satz, auswahl = "15000000", "0.03", "MAX"
            else:
                kategorie = eingaben["verstosskategorie"]
                parameter = regel["parameter"][kategorie]
                festbetrag, satz = parameter["festbetrag"], parameter["satz"]
                klasse = eingaben["akteurklasse"]
                auswahl = (
                    "FESTBETRAG"
                    if klasse == "KEIN_UNTERNEHMEN"
                    else "MIN"
                    if klasse == "KMU" or (klasse == "SMC" and kategorie != "VERBOT")
                    else "MAX"
                )
            if auswahl == "FESTBETRAG":
                wert = festbetrag
                schritte.append({"operation": auswahl, "wert": wert})
            else:
                umsatz = eingaben["weltweiter_vorjahresumsatz_eur"]
                anteil = _anteil(umsatz, satz)
                wert = _dezimaltext(
                    (min if auswahl == "MIN" else max)(
                        Decimal(festbetrag), Decimal(anteil)
                    )
                )
                schritte.extend(
                    [
                        {
                            "operation": "MULTIPLIKATION",
                            "operanden": [umsatz, satz],
                            "wert": anteil,
                        },
                        {
                            "operation": auswahl,
                            "operanden": [festbetrag, anteil],
                            "wert": wert,
                        },
                    ]
                )
        elif regel_id == "AIA_030_EINWANDSPERIODE":
            wert = {
                "anzahl": 2,
                "einheit": "WOCHE"
                if eingaben["notifizierungsgrundlage"] == "AKKREDITIERUNGSBESCHEINIGUNG"
                else "MONAT",
            }
            schritte.append(
                {
                    "operation": "AUSWAHL_EINWANDSPERIODE",
                    "grundlage": eingaben["notifizierungsgrundlage"],
                    "wert": wert.copy(),
                }
            )
        elif regel_id == "AIA_100_OBERGRENZE":
            wert = "1500000" if eingaben["verstosskategorie"] == "VERBOT" else "750000"
            schritte.append({"operation": "FESTBETRAG", "wert": wert})
        elif regel_id == "KMU_PARTNERANTEIL":
            operanden = [eingaben[name] for name in regel["eingaben"]]
            wert = _dezimaltext(max(map(Decimal, operanden)))
            schritte.append({"operation": "MAX", "operanden": operanden, "wert": wert})
        elif regel_id == "PANEL_EU_MINDESTZAHL":
            anzahl = eingaben["mitgliederzahl"]
            wert = (4 * anzahl + 4) // 5
            schritte.append(
                {
                    "operation": "AUFRUNDEN_VIER_FUENFTEL",
                    "operanden": [anzahl],
                    "wert": wert,
                }
            )
        elif regel_id == "AIA_065_005_ZWEIDRITTELMEHRHEIT":
            anzahl = eingaben["benannte_mitgliedstaatenvertreter"]
            wert = (2 * anzahl + 2) // 3
            schritte.append(
                {
                    "operation": "AUFRUNDEN_ZWEI_DRITTEL",
                    "operanden": [anzahl],
                    "wert": wert,
                }
            )
        elif regel_id == "PANEL_DRITTEL_AUTORISIERUNG":
            anzahl = eingaben["mitgliederzahl"]
            wert = (anzahl + 2) // 3
            schritte.append(
                {
                    "operation": "AUFRUNDEN_EIN_DRITTEL",
                    "operanden": [anzahl],
                    "wert": wert,
                }
            )
        elif regel_id == "PANEL_EINFACHE_MEHRHEIT":
            anzahl = eingaben["mitgliederzahl"]
            wert = anzahl // 2 + 1
            schritte.append(
                {
                    "operation": "MEHR_ALS_DIE_HAELFTE",
                    "operanden": [anzahl],
                    "wert": wert,
                }
            )
    if regel_id == "AIA_073_MELDEFRISTTAGE":
        kurz = [
            eingaben.get("weitverbreiteter_verstoss"),
            eingaben.get("schwere_irreversible_kritische_infrastrukturstoerung"),
        ]
        absatz = None
        if any(w is True for w in kurz):
            wert, absatz = 2, "ART_073/3"
            relevant = set()
        elif not relevant:
            wert, absatz = (
                (10, "ART_073/4") if eingaben["todesfall"] else (15, "ART_073/2")
            )
        schritte.append(
            {
                "operation": "PRIORISIERTE_HOECHSTDAUER",
                "fundstelle": absatz,
                "wert": wert,
            }
        )
    if regel_id in ("KMU_SCHWELLEN", "KMU_RATIONALSCHWELLEN"):
        wert = {}
        relevant = set()
        for name, personen, umsatz, bilanz in [
            ("kleinst", "10", "2000000", "2000000"),
            ("klein", "50", "10000000", "10000000"),
            ("kmu", "250", "50000000", "43000000"),
            ("smc_groessenrahmen", "750", "150000000", "129000000"),
        ]:
            p = eingaben.get("jahresarbeitseinheiten")
            u = eingaben.get("jahresumsatz_eur")
            b = eingaben.get("jahresbilanzsumme_eur")
            if regel_id == "KMU_RATIONALSCHWELLEN":
                n, d = eingaben.get("jae_zaehler"), eingaben.get("jae_nenner")
                personal = (
                    None if n is None or d is None else int(n) < int(personen) * int(d)
                )
            else:
                personal = None if p is None else Decimal(p) < Decimal(personen)
            finanz = [
                None if u is None else Decimal(u) <= Decimal(umsatz),
                None if b is None else Decimal(b) <= Decimal(bilanz),
            ]
            finanzwert = True if True in finanz else None if None in finanz else False
            wert[name] = (
                False
                if personal is False or finanzwert is False
                else None
                if personal is None or finanzwert is None
                else True
            )
            if wert[name] is None:
                if personal is None:
                    if regel_id == "KMU_RATIONALSCHWELLEN":
                        relevant.update(
                            k for k in ("jae_zaehler", "jae_nenner") if k in fehlend
                        )
                    else:
                        relevant.add("jahresarbeitseinheiten")
                if finanzwert is None:
                    relevant.update(
                        k
                        for k in ("jahresumsatz_eur", "jahresbilanzsumme_eur")
                        if k in fehlend
                    )
        schritte.append({"operation": "GROESSENMERKMALE", "wert": wert.copy()})
    unbekannt = bool(relevant)
    ergebnis.update(
        wert=wert,
        status="EINGABE_FEHLT" if unbekannt else "AUSGEWERTET",
        anwendbarkeit="UNBEKANNT",
        entscheidungsstatus="UNBESTIMMT" if unbekannt else "ENTSCHIEDEN",
        rechenschritte=schritte,
        fehlende_angaben=sorted(fehlend),
        entscheidungsrelevante_luecken=sorted(relevant),
        annahmen=[
            "Rechengröße; zeitliche und allgemeine rechtliche Anwendbarkeit separat prüfen",
            "Katalogstatus: " + regel["status"],
        ],
        hinweise=[regel["automatisierungsgrenze"]],
        nachweise=[
            {
                "art": "RECHTSQUELLE",
                "fundstelle": stelle,
                "quellenfassung": quellenfassung,
            }
            for stelle in regel["fundstellen"]
        ],
    )
    return ergebnis


def berechne_bussgeldobergrenze(eingaben, *, quellenfassung):
    """Gesetzliche Obergrenze nach Artikel 99; kein tatsächlicher Bußgeldbetrag."""
    return berechne_regel("AIA_099_OBERGRENZE", eingaben, quellenfassung=quellenfassung)
