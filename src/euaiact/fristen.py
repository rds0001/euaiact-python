"""Explizite Kalenderfristen nach VO 1182/71, ohne Systemdatum."""

import calendar as kalender_modul
from datetime import date, timedelta
import re

from .kern import _umschlag, _ganze_zahl


def _datum(text):
    if not isinstance(text, str) or not re.fullmatch(
        r"[0-9]{4}-[0-9]{2}-[0-9]{2}", text
    ):
        raise ValueError("ISO-Datum YYYY-MM-DD erforderlich")
    return date.fromisoformat(text)


def _monatsschritt(start, monate):
    """Calendar correspondence without intermediate working-day adjustment."""
    jahr, monat_null = divmod(start.year * 12 + start.month - 1 + monate, 12)
    if not 1 <= jahr <= 9999:
        raise ValueError("Zeitraum außerhalb des unterstützten ISO-Datumsbereichs")
    monat = monat_null + 1
    return date(jahr, monat, min(start.day, kalender_modul.monthrange(jahr, monat)[1]))


def berechne_frist(
    ereignisdatum, anzahl, einheit, *, modus, kalender=None, quellenfassung
):
    """Berechnet ein Enddatum mit ausdrücklich übergebenem Feiertagskalender.

    Unterstützt FRIST, FESTER_TERMIN, INKRAFTTRETEN sowie VERFAHREN_1755_TAGE und RUECKWAERTS.
    STUNDE im Modus FRIST verwendet den dokumentierten Offset-Zeitpunktvertrag.
    Ab48Stunden bleibt F011 explizit offen. Das Resultat ersetzt keine
    zusätzlich bestehende Pflicht zum unverzüglichen Handeln.
    """
    if einheit == "STUNDE":
        from .stundenfristen import _stundenfrist

        return _stundenfrist(ereignisdatum, anzahl, modus, kalender, quellenfassung)
    eingaben = dict(
        ereignisdatum=ereignisdatum,
        anzahl=anzahl,
        einheit=einheit,
        modus=modus,
        kalender=kalender,
    )
    ergebnis = _umschlag("EU_1182_71_DATUM", eingaben, quellenfassung)
    ergebnis.update(regelversion="0.1.0", ergebnistyp="DATUM", einheit="KALENDERTAG")
    if quellenfassung != "EUAIACT_2026_07_27":
        ergebnis["hinweise"] = ["Quellenfassung für diese Regel nicht verfügbar"]
        return ergebnis
    fehler = []
    fehlend = [
        name
        for name in ("ereignisdatum", "anzahl", "einheit", "modus", "kalender")
        if eingaben[name] is None
    ]
    start = None
    if ereignisdatum is not None:
        try:
            start = _datum(ereignisdatum)
        except ValueError:
            fehler.append("Ungültiges ereignisdatum")
    if anzahl is not None and (not _ganze_zahl(anzahl) or anzahl < 1):
        fehler.append("anzahl muss eine positive ganze Zahl sein")
    if einheit is not None and einheit not in (
        "TAG",
        "ARBEITSTAG",
        "WOCHE",
        "MONAT",
        "JAHR",
    ):
        fehler.append("Unzulässige Fristeinheit")
    if modus is not None and modus not in (
        "FRIST",
        "FESTER_TERMIN",
        "INKRAFTTRETEN",
        "RUECKWAERTS",
        "VERFAHREN_1755_TAGE",
    ):
        fehler.append("Unzulässiger Fristmodus")
    if (
        modus == "VERFAHREN_1755_TAGE"
        and einheit is not None
        and einheit not in ("TAG", "ARBEITSTAG")
    ):
        fehler.append("Verfahrensmodus unterstützt nur TAG und ARBEITSTAG")
    von = bis = None
    feiertage = set()
    if kalender is not None:
        if not isinstance(kalender, dict) or set(kalender) != {
            "von",
            "bis",
            "feiertage",
            "bezug",
        }:
            fehler.append("Kalender benötigt genau von, bis, feiertage und bezug")
        else:
            try:
                von, bis = _datum(kalender["von"]), _datum(kalender["bis"])
                if von > bis:
                    raise ValueError()
                if (
                    not isinstance(kalender["bezug"], str)
                    or not kalender["bezug"].strip()
                ):
                    raise ValueError()
                if not isinstance(kalender["feiertage"], list):
                    raise ValueError()
                tage = [_datum(tag) for tag in kalender["feiertage"]]
                if len(set(tage)) != len(tage) or any(
                    not von <= tag <= bis for tag in tage
                ):
                    raise ValueError()
                feiertage = set(tage)
            except (ValueError, TypeError):
                fehler.append("Ungültiger oder widersprüchlicher Kalender")
    if fehler:
        ergebnis["hinweise"] = fehler
        return ergebnis
    if anzahl is not None:
        anzahl = int(anzahl)
        ergebnis["eingaben"]["anzahl"] = anzahl
    kalender_noetig = (
        modus in ("FRIST", "VERFAHREN_1755_TAGE", "RUECKWAERTS")
        or einheit == "ARBEITSTAG"
    )
    relevant = [name for name in fehlend if name != "kalender" or kalender_noetig]
    if relevant:
        ergebnis.update(
            status="EINGABE_FEHLT",
            anwendbarkeit="UNBEKANNT",
            entscheidungsstatus="UNBESTIMMT",
            fehlende_angaben=fehlend,
            entscheidungsrelevante_luecken=relevant,
        )
        return ergebnis

    class Kalenderluecke(Exception):
        pass

    def arbeitstag(tag):
        if not von <= tag <= bis:
            raise Kalenderluecke()
        return tag.weekday() < 5 and tag not in feiertage

    schritte = []
    richtung = -1 if modus == "RUECKWAERTS" else 1
    try:
        if modus == "VERFAHREN_1755_TAGE":
            beginn = start + timedelta(days=1)
            while not arbeitstag(beginn):
                beginn += timedelta(days=1)
            start = beginn - timedelta(days=1)
            schritte.append(
                {
                    "operation": "VERFAHRENSBEGINN_ERSTER_ARBEITSTAG",
                    "ereignisdatum": ereignisdatum,
                    "beginn": beginn.isoformat(),
                    "rechenanker": start.isoformat(),
                }
            )
        if anzahl > (
            (date.max - start).days if richtung == 1 else (start - date.min).days
        ):
            raise ValueError("Zeitraum außerhalb des unterstützten ISO-Datumsbereichs")
        if einheit in ("TAG", "WOCHE"):
            ende = start + timedelta(
                days=richtung * anzahl * (7 if einheit == "WOCHE" else 1)
            )
        elif einheit == "ARBEITSTAG":
            ende, gezaehlt = start, 0
            while gezaehlt < anzahl:
                ende += timedelta(days=richtung)
                if arbeitstag(ende):
                    gezaehlt += 1
        else:
            monate = richtung * anzahl * (12 if einheit == "JAHR" else 1)
            ende = _monatsschritt(start, monate)
        schritte.append({"operation": "KALENDARISCHES_ENDE", "wert": ende.isoformat()})
        mindesttage = anzahl >= 2 if einheit in ("TAG", "ARBEITSTAG") else True
        if modus == "RUECKWAERTS":
            # Artikel 3(4) Satz 2 nimmt nur die Endverschiebung aus, nicht Absatz 5.
            arbeitstage, tag = 0, start
            if mindesttage:
                while tag > ende and arbeitstage < 2:
                    tag -= timedelta(days=1)
                    if arbeitstag(tag):
                        arbeitstage += 1
                while arbeitstage < 2:
                    ende -= timedelta(days=1)
                    if arbeitstag(ende):
                        arbeitstage += 1
            schritte.append(
                {
                    "operation": "RUECKWAERTS_MINDESTARBEITSTAGE",
                    "wert": ende.isoformat(),
                }
            )
        if modus in ("FRIST", "VERFAHREN_1755_TAGE"):
            while not arbeitstag(ende):
                ende += timedelta(days=1)
            if mindesttage:
                tag, arbeitstage = start, 0
                while tag < ende and arbeitstage < 2:
                    tag += timedelta(days=1)
                    if arbeitstag(tag):
                        arbeitstage += 1
                while arbeitstage < 2:
                    ende += timedelta(days=1)
                    if arbeitstag(ende):
                        arbeitstage += 1
            schritte.append(
                {"operation": "ARBEITSTAGSREGELN", "wert": ende.isoformat()}
            )
    except Kalenderluecke:
        ergebnis.update(
            status="EINGABE_FEHLT",
            anwendbarkeit="UNBEKANNT",
            entscheidungsstatus="UNBESTIMMT",
            fehlende_angaben=["kalenderdeckung"],
            entscheidungsrelevante_luecken=["kalenderdeckung"],
            hinweise=["Der übergebene Kalender deckt nicht alle benötigten Tage ab"],
        )
        return ergebnis
    except (ValueError, OverflowError):
        ergebnis["hinweise"] = [
            "Zeitraum außerhalb des unterstützten ISO-Datumsbereichs"
        ]
        return ergebnis
    ergebnis.update(
        wert=ende.isoformat(),
        status="AUSGEWERTET",
        anwendbarkeit="UNBEKANNT",
        entscheidungsstatus="ENTSCHIEDEN",
        rechenschritte=schritte,
        fehlende_angaben=fehlend,
        annahmen=[
            "Expliziter Nutzerkalender"
            if kalender_noetig
            else "Kalenderunabhängiger Datumsmodus",
            "Fristberechnung; konkrete rechtliche Anwendbarkeit separat prüfen",
        ],
        hinweise=[
            "Beginn des Ergebnistags"
            if modus == "INKRAFTTRETEN"
            else "Ablauf des Ergebnistags",
            "Eine zusätzliche Pflicht zum unverzüglichen Handeln wird nicht bewertet",
        ],
        nachweise=[
            {
                "art": "RECHTSQUELLE",
                "fundstelle": "31971R1182/ART_2_BIS_5",
                "quellenfassung": quellenfassung,
            }
        ],
    )
    if modus == "VERFAHREN_1755_TAGE":
        ergebnis["nachweise"].append(
            {
                "art": "RECHTSQUELLE",
                "fundstelle": "32026R1755/ART_012/2",
                "quellenfassung": quellenfassung,
            }
        )
        ergebnis["hinweise"].append(
            "Sondermodus nur für einschlägiges GPAI-Kommissionsverfahren"
        )
    return ergebnis
