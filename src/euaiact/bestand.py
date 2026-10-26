"""Bestandsfristen nach Artikel 111(1), (3), (4), ohne Gesamtgeltungsurteil."""

from .fristen import _datum
from .kern import _umschlag

_FALLGRUPPEN = {
    "GROSS_IT_ANHANG_X": (
        "2027-08-02",
        "2030-12-31",
        ("inverkehrbringen", "inbetriebnahme"),
        "ART_111/1",
    ),
    "GPAI_MODELL": ("2025-08-02", "2027-08-02", ("inverkehrbringen",), "ART_111/3"),
    "SYNTHETISCHE_AUSGABEN_ART_50_2": (
        "2026-08-02",
        "2026-12-02",
        ("inverkehrbringen",),
        "ART_111/4",
    ),
}
_FASSUNGEN = {"EUAIACT_2024_08_01": "2024-08-01", "EUAIACT_2026_07_27": "2026-07-27"}


def pruefe_bestandsfrist(fallgruppe, stichtag, *, ereignisse, quellenfassung):
    """Qualifizierte Fallgruppe und eigene Ereignisdaten gegen feste Termine prüfen."""
    from .hochrisikobestand import GRUPPEN, _pruefe_hochrisikobestand

    if isinstance(fallgruppe, str) and fallgruppe in GRUPPEN:
        return _pruefe_hochrisikobestand(
            fallgruppe, stichtag, ereignisse, quellenfassung
        )
    ergebnis = _umschlag(
        "AIA_111_BESTANDSFRIST",
        {
            "fallgruppe": fallgruppe,
            "stichtag": stichtag,
            "ereignisse": ereignisse,
        },
        quellenfassung,
    )
    ergebnis.update(regelversion="0.1.0", ergebnistyp="OBJEKT")
    fehler = []
    if not isinstance(quellenfassung, str) or quellenfassung not in _FASSUNGEN:
        fehler.append("Quellenfassung für diese Regel nicht verfügbar")
    if fallgruppe is not None and (
        not isinstance(fallgruppe, str)
        or fallgruppe not in _FALLGRUPPEN
        or (
            fallgruppe == "SYNTHETISCHE_AUSGABEN_ART_50_2"
            and quellenfassung == "EUAIACT_2024_08_01"
        )
    ):
        fehler.append("Fallgruppe in dieser Quellenfassung nicht verfügbar")
    datum = None
    if stichtag is not None:
        try:
            datum = _datum(stichtag)
            if (
                isinstance(quellenfassung, str)
                and quellenfassung in _FASSUNGEN
                and datum < _datum(_FASSUNGEN[quellenfassung])
            ):
                fehler.append(
                    "Stichtag liegt vor Inkrafttreten der gewählten Quellenfassung"
                )
        except ValueError:
            fehler.append("Ungültiger stichtag")
    daten = {} if ereignisse is None else ereignisse
    if not isinstance(daten, dict):
        fehler.append("ereignisse muss ein Objekt sein")
    else:
        if any(k not in ("inverkehrbringen", "inbetriebnahme") for k in daten):
            fehler.append("Unbekanntes Ereignisfeld")
        for name in ("inverkehrbringen", "inbetriebnahme"):
            ereignis = daten.get(name)
            if ereignis is None:
                continue
            if not isinstance(ereignis, dict) or any(
                k not in ("erfolgt", "datum") for k in ereignis
            ):
                fehler.append(f"Ungültiges Ereignisobjekt: {name}")
                continue
            erfolgt, zeitpunkt = ereignis.get("erfolgt"), ereignis.get("datum")
            if erfolgt is not None and type(erfolgt) is not bool:
                fehler.append(f"Ungültiger Ereignisstatus: {name}")
            if zeitpunkt is not None:
                if erfolgt is not True:
                    fehler.append(f"Ereignisdatum verlangt erfolgt=true: {name}")
                try:
                    ereignisdatum = _datum(zeitpunkt)
                    if datum is not None and ereignisdatum > datum:
                        fehler.append(f"Ereignis nach Stichtag: {name}")
                except ValueError:
                    fehler.append(f"Ungültiges Ereignisdatum: {name}")
    if fehler:
        ergebnis["hinweise"] = fehler
        return ergebnis
    fehlend = [
        k for k, v in (("fallgruppe", fallgruppe), ("stichtag", stichtag)) if v is None
    ]
    ergebnis.update(
        anwendbarkeit="UNBEKANNT",
        entscheidungsstatus="UNBESTIMMT",
        status="EINGABE_FEHLT",
    )
    if fehlend:
        ergebnis.update(
            fehlende_angaben=fehlend, entscheidungsrelevante_luecken=fehlend
        )
        return ergebnis
    grenze, frist, namen, fundstelle = _FALLGRUPPEN[fallgruppe]
    werte, schritte = [], []
    for name in namen:
        ereignis = daten.get(name) or {}
        erfolgt, zeitpunkt = ereignis.get("erfolgt"), ereignis.get("datum")
        wert = None
        if erfolgt is False:
            wert = False
        elif erfolgt is True and zeitpunkt is not None:
            wert = _datum(zeitpunkt) < _datum(grenze)
        else:
            fehlend.append(
                f"ereignisse.{name}." + ("erfolgt" if erfolgt is None else "datum")
            )
        werte.append(wert)
        schritte.append(
            {
                "operation": "EREIGNIS_VOR_BESTANDSGRENZE",
                "ereignis": name,
                "erfolgt": erfolgt,
                "datum": zeitpunkt,
                "bestandsgrenze": grenze,
                "wert": wert,
            }
        )
    bestand = True if True in werte else (None if None in werte else False)
    lage = "UNBESTIMMT" if bestand is None else "KEINE_BESTANDSFRIST"
    if bestand is True:
        lage = (
            "VOR_FRISTTAG"
            if datum < _datum(frist)
            else ("FRISTTAG" if datum == _datum(frist) else "NACH_FRISTTAG")
        )
    ergebnis.update(
        wert={
            "bestand": bestand,
            "erfuellungsfrist": frist if bestand is True else None,
            "friststatus": lage,
        },
        status="EINGABE_FEHLT" if bestand is None else "AUSGEWERTET",
        entscheidungsstatus="UNBESTIMMT" if bestand is None else "ENTSCHIEDEN",
        fehlende_angaben=fehlend,
        entscheidungsrelevante_luecken=fehlend if bestand is None else [],
        entscheidungsschritte=schritte
        + [
            {"operation": "BESTAND_ALTERNATIVE", "wert": bestand},
            {
                "operation": "FESTER_ERFUELLUNGSTERMIN",
                "stichtag": stichtag,
                "fristtag": frist,
                "friststatus": lage,
            },
        ],
        annahmen=[
            "Fallgruppe ausdrücklich qualifiziert; Ereignisse gelten zum Stichtag"
        ],
        hinweise=[
            "Artikel 2, Artikel 5 und tatsächliche Pflichterfüllung separat prüfen",
            "Keine Wochenendverschiebung gesetzlicher fester Termine; Artikel 111 Absatz 2 nicht enthalten",
        ],
        nachweise=[
            {
                "art": "RECHTSQUELLE",
                "fundstelle": fundstelle,
                "quellenfassung": quellenfassung,
            }
        ],
    )
    return ergebnis
