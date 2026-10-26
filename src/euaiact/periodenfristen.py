"""Whole long periods, month fractions and explicitly qualified1755 start profiles."""

from datetime import timedelta
from .kern import _umschlag, _ganze_zahl
from .fristen import _datum, _monatsschritt, berechne_frist
from .rechnen import berechne_regel


def berechne_periodenfrist(
    ereignisdatum,
    anzahl,
    einheit,
    *,
    modus,
    kalender=None,
    monatsbruch=None,
    beginnkonvention=None,
    beginnbegruendung=None,
    quellenfassung,
):
    """Compose a whole week/month/year period and an optional proper month fraction.

    Calendar end rules apply once to the complete period. Non-integral fraction
    days have no assumed sub-day legal end convention. F007 requires an explicit
    justified start profile for1755 long periods; no profile is selected silently.
    """
    inputs = dict(
        ereignisdatum=ereignisdatum,
        anzahl=anzahl,
        einheit=einheit,
        modus=modus,
        kalender=kalender,
        monatsbruch=monatsbruch,
        beginnkonvention=beginnkonvention,
        beginnbegruendung=beginnbegruendung,
    )
    out = _umschlag("EU_1182_71_GESAMTPERIODE", inputs, quellenfassung)
    out.update(regelversion="0.1.0", ergebnistyp="DATUM", einheit="KALENDERTAG")
    if quellenfassung != "EUAIACT_2026_07_27":
        out["hinweise"] = ["Quellenfassung fuer diese Regel nicht verfuegbar"]
        return out
    errors = []
    event = None
    if ereignisdatum is not None:
        try:
            event = _datum(ereignisdatum)
        except (ValueError, TypeError):
            errors.append("Gueltiges Ereignisdatum YYYY-MM-DD erforderlich")
    if anzahl is not None and (not _ganze_zahl(anzahl) or not 0 <= anzahl <= 1000000):
        errors.append("anzahl muss eine ganze Zahl zwischen 0 und 1000000 sein")
    if einheit is not None and (
        not isinstance(einheit, str) or einheit not in {"WOCHE", "MONAT", "JAHR"}
    ):
        errors.append("Gesamtperiodenvertrag erfordert WOCHE, MONAT oder JAHR")
    modes = {"FRIST", "FESTER_TERMIN", "INKRAFTTRETEN", "RUECKWAERTS", "VERFAHREN_1755"}
    if modus is not None and (not isinstance(modus, str) or modus not in modes):
        errors.append("Unzulaessiger Gesamtperiodenmodus")
    if beginnkonvention is not None and (
        not isinstance(beginnkonvention, str)
        or beginnkonvention not in {"EREIGNISTAG", "BEGINNTAG", "VORTAG_DES_BEGINNS"}
    ):
        errors.append("Unzulaessige Beginnkonvention")
    if beginnbegruendung is not None and (
        not isinstance(beginnbegruendung, str) or not beginnbegruendung.strip()
    ):
        errors.append("Nichtleere lokale Begruendung der Beginnkonvention erforderlich")
    if modus != "VERFAHREN_1755" and (
        beginnkonvention is not None or beginnbegruendung is not None
    ):
        errors.append("Beginnprofil nur im Modus VERFAHREN_1755 zulaessig")
    if kalender is not None:
        check = berechne_frist(
            "2000-01-01",
            1,
            "TAG",
            modus="FESTER_TERMIN",
            kalender=kalender,
            quellenfassung=quellenfassung,
        )
        if check["status"] == "EINGABE_UNGUELTIG":
            errors.append("Ungueltiger Kalender")
    fraction = None
    fraction_missing = []
    if monatsbruch is not None:
        if einheit != "MONAT":
            errors.append("Monatsbruch nur mit Einheit MONAT zulaessig")
        if not isinstance(monatsbruch, dict) or set(monatsbruch) != {
            "zaehler",
            "nenner",
        }:
            errors.append(
                "Monatsbruch benoetigt genau zaehler und nenner als Ganzzahltexte"
            )
        else:
            check = berechne_regel(
                "EU_1182_MONATSBRUCH_TAGE",
                dict(
                    monatsbruch_zaehler=monatsbruch["zaehler"],
                    monatsbruch_nenner=monatsbruch["nenner"],
                ),
                quellenfassung=quellenfassung,
            )
            if check["status"] == "EINGABE_UNGUELTIG":
                errors.append("Ungueltiger echter Monatsbruch")
            elif check["status"] == "EINGABE_FEHLT":
                fraction_missing = [
                    "monatsbruch." + k
                    for k in ("zaehler", "nenner")
                    if monatsbruch[k] is None
                ]
            else:
                fraction = check["wert"]
    if (
        not errors
        and anzahl == 0
        and not fraction_missing
        and (fraction is None or fraction["zaehler"] == "0")
    ):
        errors.append("Gesamtperiode muss positiv sein")
    if errors:
        out["hinweise"] = errors
        return out
    if anzahl is not None:
        anzahl = int(anzahl)
        out["eingaben"]["anzahl"] = anzahl
    needs_calendar = modus in {"FRIST", "RUECKWAERTS", "VERFAHREN_1755"}
    missing = [
        k for k in ("ereignisdatum", "anzahl", "einheit", "modus") if inputs[k] is None
    ] + fraction_missing
    if needs_calendar and kalender is None:
        missing.append("kalender")
    if missing:
        out.update(
            status="EINGABE_FEHLT",
            anwendbarkeit="UNBEKANNT",
            entscheidungsstatus="UNBESTIMMT",
            fehlende_angaben=sorted(missing),
            entscheidungsrelevante_luecken=sorted(missing),
        )
        return out
    out["nachweise"] = [
        dict(
            art="RECHTSQUELLE",
            fundstelle="31971R1182/ART_2_BIS_5",
            quellenfassung=quellenfassung,
        )
    ]
    if monatsbruch is not None:
        out["nachweise"].append(
            dict(
                art="RECHTSQUELLE",
                fundstelle="31971R1182/ART_3/2/d",
                quellenfassung=quellenfassung,
            )
        )
    if modus == "VERFAHREN_1755":
        out["nachweise"].append(
            dict(
                art="RECHTSQUELLE",
                fundstelle="32026R1755/ART_12/2",
                quellenfassung=quellenfassung,
            )
        )
        if beginnkonvention is None or beginnbegruendung is None:
            out.update(
                status="REGEL_UNGEKLAERT",
                anwendbarkeit="UNBEKANNT",
                entscheidungsstatus="UNBESTIMMT",
                hinweise=[
                    "F007: Langperiodenbeginn erfordert ausdruecklich begruendete Nutzervorgabe"
                ],
            )
            return out
        out["nutzervorgaben"] = dict(
            beginnkonvention=beginnkonvention, beginnbegruendung=beginnbegruendung
        )
    if fraction is not None and fraction["nenner"] != "1":
        out.update(
            status="REGEL_UNGEKLAERT",
            anwendbarkeit="UNBEKANNT",
            entscheidungsstatus="UNBESTIMMT",
            hinweise=[
                "Monatsbruch ergibt nichtganze Tage; untertaegige Endkonvention nicht qualifiziert. Keine Rundung."
            ],
            rechenschritte=[dict(operation="EXAKTER_MONATSBRUCH_TAGE", wert=fraction)],
        )
        return out
    try:
        anchor = count_anchor = event
        steps = []
        if modus == "VERFAHREN_1755":
            first = berechne_frist(
                ereignisdatum,
                1,
                "ARBEITSTAG",
                modus="FESTER_TERMIN",
                kalender=kalender,
                quellenfassung=quellenfassung,
            )
            if first["status"] != "AUSGEWERTET":
                out.update(
                    {
                        k: first[k]
                        for k in (
                            "status",
                            "anwendbarkeit",
                            "entscheidungsstatus",
                            "hinweise",
                            "fehlende_angaben",
                            "entscheidungsrelevante_luecken",
                        )
                    }
                )
                return out
            begin = _datum(first["wert"])
            count_anchor = begin - timedelta(days=1)
            anchor = (
                event
                if beginnkonvention == "EREIGNISTAG"
                else begin
                if beginnkonvention == "BEGINNTAG"
                else count_anchor
            )
            steps.append(
                dict(
                    operation="QUALIFIZIERTER_VERFAHRENSBEGINN",
                    beginn=begin.isoformat(),
                    rechenanker=anchor.isoformat(),
                    zaehlanker=count_anchor.isoformat(),
                )
            )
        direction = -1 if modus == "RUECKWAERTS" else 1
        whole = (
            anchor + timedelta(days=direction * anzahl * 7)
            if einheit == "WOCHE"
            else _monatsschritt(
                anchor, direction * anzahl * (12 if einheit == "JAHR" else 1)
            )
        )
        steps.append(
            dict(
                operation="GANZE_KALENDERPERIODE",
                anzahl=anzahl,
                einheit=einheit,
                wert=whole.isoformat(),
            )
        )
        extra = 0 if fraction is None else int(fraction["zaehler"])
        nominal = whole + timedelta(days=direction * extra)
        if fraction is not None:
            steps.append(
                dict(
                    operation="MONATSBRUCH_NACH_GANZEN_MONATEN",
                    tage=fraction,
                    wert=nominal.isoformat(),
                )
            )
        if needs_calendar:
            distance = direction * (nominal - count_anchor).days
            distance = max(2 if anzahl > 0 or extra >= 2 else 1, distance)
            # Delegate once for the COMPLETE nominal period, never each component.
            final = berechne_frist(
                count_anchor.isoformat(),
                distance,
                "TAG",
                modus="RUECKWAERTS" if direction < 0 else "FRIST",
                kalender=kalender,
                quellenfassung=quellenfassung,
            )
            if final["status"] != "AUSGEWERTET":
                out.update(
                    {
                        k: final[k]
                        for k in (
                            "status",
                            "anwendbarkeit",
                            "entscheidungsstatus",
                            "hinweise",
                            "fehlende_angaben",
                            "entscheidungsrelevante_luecken",
                        )
                    }
                )
                return out
            end = final["wert"]
            steps.append(
                dict(operation="ARBEITSTAGSREGELN_NUR_GESAMTPERIODE", wert=end)
            )
        else:
            end = nominal.isoformat()
    except (ValueError, OverflowError):
        out["hinweise"] = [
            "Gesamtperiode ausserhalb Datumsbereich oder ohne positive Laufzeit ab qualifiziertem Beginn"
        ]
        return out
    out.update(
        wert=end,
        status="AUSGEWERTET",
        anwendbarkeit="UNBEKANNT",
        entscheidungsstatus="ENTSCHIEDEN",
        rechenschritte=steps,
        annahmen=[
            "Normmodus, Beginnprofil und Monatsbruch ausdruecklich qualifiziert; kein Systemdatum"
        ],
        hinweise=[
            "Beginn des Ergebnistags"
            if modus == "INKRAFTTRETEN"
            else "Ablauf des Ergebnistags",
            "Keine Aussage zur unverzueglichen Handlungspflicht oder allgemeinen Anwendbarkeit",
        ],
    )
    return out
