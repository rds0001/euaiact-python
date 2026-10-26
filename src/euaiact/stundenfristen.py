"""Whole-hour periods with explicit offset and an unresolved long-period boundary."""

from datetime import date, timedelta
from .kern import _umschlag, _ganze_zahl
from .zeitpunkte import _zeitpunktteile

_MAX_SEKUNDEN = date.max.toordinal() * 86400


def _utc_text(sekunden):
    if not 0 <= sekunden < _MAX_SEKUNDEN:
        raise ValueError("Datumsbereich")
    tage, rest = divmod(sekunden, 86400)
    tag = date.min + timedelta(days=tage)
    stunde, rest = divmod(rest, 3600)
    minute, sekunde = divmod(rest, 60)
    return f"{tag.isoformat()}T{stunde:02}:{minute:02}:{sekunde:02}Z"


def _stundenfrist(ereignisdatum, anzahl, modus, kalender, quellenfassung):
    eingaben = dict(
        ereignisdatum=ereignisdatum,
        anzahl=anzahl,
        einheit="STUNDE",
        modus=modus,
        kalender=kalender,
    )
    ergebnis = _umschlag("EU_1182_71_STUNDE", eingaben, quellenfassung)
    ergebnis.update(regelversion="0.1.0", ergebnistyp="OBJEKT", einheit="STUNDE")
    if quellenfassung != "EUAIACT_2026_07_27":
        ergebnis["hinweise"] = ["Quellenfassung fuer diese Regel nicht verfuegbar"]
        return ergebnis
    fehler = []
    teile = None
    if ereignisdatum is not None:
        try:
            teile = _zeitpunktteile(ereignisdatum)
        except ValueError:
            fehler.append(
                "Gueltiger Ereigniszeitpunkt mit explizitem Offset erforderlich"
            )
    if anzahl is not None and (
        not _ganze_zahl(anzahl) or not 1 <= anzahl <= _MAX_SEKUNDEN // 3600
    ):
        fehler.append(
            "anzahl muss eine positive ganze Stundenzahl im Datumsbereich sein"
        )
    if modus is not None and modus != "FRIST":
        fehler.append("Stundenvertrag unterstuetzt nur den allgemeinen Modus FRIST")
    if kalender is not None:
        # Reuse the existing complete calendar validator in a calendar-independent
        # fixed-date call. Its result is not used as a legal date or time anchor.
        from .fristen import berechne_frist

        test = berechne_frist(
            "2000-01-01",
            1,
            "TAG",
            modus="FESTER_TERMIN",
            kalender=kalender,
            quellenfassung=quellenfassung,
        )
        if test["status"] == "EINGABE_UNGUELTIG":
            fehler.extend(test["hinweise"])
    if fehler:
        ergebnis["hinweise"] = fehler
        return ergebnis
    if anzahl is not None:
        anzahl = int(anzahl)
        ergebnis["eingaben"]["anzahl"] = anzahl
    fehlend = [k for k in ("ereignisdatum", "anzahl", "modus") if eingaben[k] is None]
    if fehlend:
        ergebnis.update(
            status="EINGABE_FEHLT",
            anwendbarkeit="UNBEKANNT",
            entscheidungsstatus="UNBESTIMMT",
            fehlende_angaben=fehlend,
            entscheidungsrelevante_luecken=fehlend,
        )
        return ergebnis
    beginn = (
        teile[0] - int(ereignisdatum[14:16]) * 60 - int(ereignisdatum[17:19]) + 3600
    )
    ende = beginn + anzahl * 3600
    try:
        start_text, end_text = _utc_text(beginn), _utc_text(ende)
    except ValueError:
        ergebnis["hinweise"] = [
            "Zeitraum ausserhalb des unterstuetzten ISO-Datumsbereichs"
        ]
        return ergebnis
    ergebnis["nachweise"] = [
        {
            "art": "RECHTSQUELLE",
            "fundstelle": "31971R1182/ART_2_BIS_5",
            "quellenfassung": quellenfassung,
        }
    ]
    if anzahl >= 48:
        ergebnis.update(
            status="REGEL_UNGEKLAERT",
            anwendbarkeit="UNBEKANNT",
            entscheidungsstatus="UNBESTIMMT",
            entscheidungsschritte=[
                {"operation": "OFFENE_RECHTSFRAGE", "frage_id": "F011", "wert": None}
            ],
            hinweise=[
                "F011: Wechselwirkung von Stundenperioden ab48Stunden mit mindestens zwei Arbeitstagen offen; kein rechtliches Fristende ausgegeben."
            ],
        )
        return ergebnis
    ergebnis.update(
        wert={"beginn": start_text, "ende_exklusiv": end_text},
        status="AUSGEWERTET",
        anwendbarkeit="UNBEKANNT",
        entscheidungsstatus="ENTSCHIEDEN",
        rechenschritte=[
            {
                "operation": "EREIGNISSTUNDE_AUSSCHLIESSEN",
                "ereigniszeitpunkt": ereignisdatum,
                "beginn": start_text,
            },
            {"operation": "VOLLE_STUNDEN", "anzahl": anzahl, "ende_exklusiv": end_text},
        ],
        annahmen=[
            "Allgemeine Stundenfrist nach1182/71; keine automatische Wahl fuer spezielle AI-Act-Hoechstgrenzen"
        ],
        hinweise=[
            "Endgrenze exklusiv; an diesem Zeitpunkt ist die Frist abgelaufen",
            "Keine Wochenend-Endverschiebung bei Stundenfristen",
            "Zusaetzliche Pflicht zum unverzueglichen Handeln separat",
        ],
    )
    return ergebnis
