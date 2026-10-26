"""Article 111(2): event history and separate public-authority deadline."""

from .fristen import _datum
from .kern import _umschlag

GRUPPEN = ("HOCHRISIKO_ANHANG_I", "HOCHRISIKO_ANHANG_III", "HOCHRISIKO_DOPPELT")
FASSUNGEN = {"EUAIACT_2024_08_01": "2024-08-01", "EUAIACT_2026_07_27": "2026-07-27"}


def _pruefe_hochrisikobestand(fallgruppe, stichtag, ereignisse, quellenfassung):
    ergebnis = _umschlag(
        "AIA_111_BESTANDSFRIST",
        dict(fallgruppe=fallgruppe, stichtag=stichtag, ereignisse=ereignisse),
        quellenfassung,
    )
    ergebnis.update(regelversion="0.1.0", ergebnistyp="OBJEKT")
    fehler = []
    if not isinstance(quellenfassung, str) or quellenfassung not in FASSUNGEN:
        fehler.append("Quellenfassung für diese Regel nicht verfügbar")
    datum = None
    if stichtag is not None:
        try:
            datum = _datum(stichtag)
            if (
                isinstance(quellenfassung, str)
                and quellenfassung in FASSUNGEN
                and datum < _datum(FASSUNGEN[quellenfassung])
            ):
                fehler.append(
                    "Stichtag liegt vor Inkrafttreten der gewählten Quellenfassung"
                )
        except ValueError:
            fehler.append("Ungültiger stichtag")
    daten = {} if ereignisse is None else ereignisse
    namen = ("inverkehrbringen", "inbetriebnahme")
    flags = (
        "aenderungshistorie_vollstaendig",
        "fuer_behoerden_bestimmt",
        "anbieter_oder_betreiber",
    )

    def boolpruefung(wert, pfad):
        if wert is not None and type(wert) is not bool:
            fehler.append("Boolescher Wert erforderlich: " + pfad)

    def datumspruefung(wert, pfad):
        if wert is not None:
            try:
                tag = _datum(wert)
                if datum is not None and tag > datum:
                    fehler.append("Ereignis nach Stichtag: " + pfad)
            except ValueError:
                fehler.append("Ungültiges Ereignisdatum: " + pfad)

    if not isinstance(daten, dict):
        fehler.append("ereignisse muss ein Objekt sein")
    else:
        if any(k not in (*namen, *flags, "aenderungen") for k in daten):
            fehler.append("Unbekanntes Ereignisfeld")
        for name in namen:
            e = daten.get(name)
            if e is None:
                continue
            if not isinstance(e, dict) or any(k not in ("erfolgt", "datum") for k in e):
                fehler.append("Ungültiges Ereignisobjekt: " + name)
                continue
            boolpruefung(e.get("erfolgt"), name + ".erfolgt")
            if e.get("datum") is not None and e.get("erfolgt") is not True:
                fehler.append("Ereignisdatum verlangt erfolgt=true: " + name)
            datumspruefung(e.get("datum"), name)
        for name in flags:
            boolpruefung(daten.get(name), name)
        aenderungen = daten.get("aenderungen")
        if aenderungen is not None:
            if not isinstance(aenderungen, list):
                fehler.append("aenderungen muss eine Liste sein")
            else:
                for i, e in enumerate(aenderungen):
                    pfad = f"aenderungen[{i}]"
                    if not isinstance(e, dict) or any(
                        k not in ("datum", "erheblich") for k in e
                    ):
                        fehler.append("Ungültiges Änderungsobjekt: " + pfad)
                        continue
                    boolpruefung(e.get("erheblich"), pfad + ".erheblich")
                    datumspruefung(e.get("datum"), pfad)
    if fehler:
        ergebnis["hinweise"] = fehler
        return ergebnis
    ergebnis.update(
        anwendbarkeit="UNBEKANNT",
        entscheidungsstatus="UNBESTIMMT",
        status="EINGABE_FEHLT",
    )
    if datum is None:
        ergebnis.update(
            fehlende_angaben=["stichtag"], entscheidungsrelevante_luecken=["stichtag"]
        )
        return ergebnis
    fehlend = set()

    def unbekannt(pfad):
        fehlend.add(pfad)
        return None, {pfad}

    def fakt(wert, pfad):
        return unbekannt(pfad) if wert is None else (wert, set())

    def verknuepfen(werte, und=False):
        entscheidend = False if und else True
        if any(w is entscheidend for w, _ in werte):
            return entscheidend, set()
        luecken = set().union(*(luecke for _, luecke in werte))
        return (
            (None, luecken)
            if any(w is None for w, _ in werte)
            else (not entscheidend, set())
        )

    oeffentlich = fakt(
        daten.get("fuer_behoerden_bestimmt"), "ereignisse.fuer_behoerden_bestimmt"
    )
    rolle = fakt(
        daten.get("anbieter_oder_betreiber"), "ereignisse.anbieter_oder_betreiber"
    )
    grenzen = (
        ["2026-08-02"]
        if quellenfassung == "EUAIACT_2024_08_01"
        else (
            ["2028-08-02"]
            if fallgruppe == GRUPPEN[0]
            else ["2027-12-02"]
            if fallgruppe == GRUPPEN[1]
            else ["2027-12-02", "2028-08-02"]
        )
    )
    kandidaten, relevante = [], set()
    for grenze in grenzen:
        ereigniswerte = []
        for name in namen:
            e = daten.get(name) or {}
            erfolgt = fakt(e.get("erfolgt"), "ereignisse." + name + ".erfolgt")
            if erfolgt[0] is True:
                wert = (
                    unbekannt("ereignisse." + name + ".datum")
                    if e.get("datum") is None
                    else (e["datum"] < grenze, set())
                )
            else:
                wert = erfolgt
            ereigniswerte.append(wert)
        bestand = verknuepfen(ereigniswerte)
        wechsel = []
        if stichtag >= grenze:
            aenderungen = daten.get("aenderungen")
            if aenderungen is None:
                wechsel.append(unbekannt("ereignisse.aenderungen"))
            else:
                for i, e in enumerate(aenderungen):
                    pfad = f"ereignisse.aenderungen[{i}]"
                    erheblich = fakt(e.get("erheblich"), pfad + ".erheblich")
                    tag = (
                        unbekannt(pfad + ".datum")
                        if e.get("datum") is None
                        else (e["datum"] >= grenze, set())
                    )
                    wechsel.append(verknuepfen([erheblich, tag], und=True))
            if daten.get("aenderungshistorie_vollstaendig") is not True:
                wechsel.append(
                    unbekannt(
                        "ereignisse.aenderungen"
                        if daten.get("aenderungshistorie_vollstaendig") is False
                        else "ereignisse.aenderungshistorie_vollstaendig"
                    )
                )
        aenderung = verknuepfen(wechsel)
        ausgeloest = verknuepfen([bestand, aenderung], und=True)
        behoerde = verknuepfen([bestand, oeffentlich, rolle], und=True)
        for wert in (bestand, ausgeloest, behoerde):
            relevante.update(wert[1])
        lage = "UNBESTIMMT" if behoerde[0] is None else "KEINE_BEHOERDENFRIST"
        if behoerde[0] is True:
            lage = (
                "VOR_FRISTTAG"
                if stichtag < "2030-08-02"
                else "FRISTTAG"
                if stichtag == "2030-08-02"
                else "NACH_FRISTTAG"
            )
        kandidaten.append(
            dict(
                bestand=bestand[0],
                aenderungsvorbehalt_ausgeloest=ausgeloest[0],
                behoerdenfrist_betroffen=behoerde[0],
                erfuellungsfrist="2030-08-02" if behoerde[0] is True else None,
                friststatus=lage,
            )
        )
    wert = dict(kandidaten[0])
    abweichend = []
    for feld in wert:
        if any(k[feld] != wert[feld] for k in kandidaten[1:]):
            abweichend.append(feld)
            wert[feld] = "UNBESTIMMT" if feld == "friststatus" else None
    hinweise = [
        "Artikel 2, Artikel 5, Artikel 113 und tatsächliche Pflichterfüllung separat prüfen",
        "Kein Bestand bedeutet kein Privileg aus Absatz 2; keine Aussage zur allgemeinen Anwendbarkeit",
    ]
    if abweichend:
        hinweise.append(
            "Offene Rechtsfrage F004: unterschiedliche Bestandsstichtage bei doppelter Hochrisikoeinstufung"
        )
    ergebnis.update(
        wert=wert,
        status="REGEL_UNGEKLAERT"
        if abweichend
        else "EINGABE_FEHLT"
        if relevante
        else "AUSGEWERTET",
        entscheidungsstatus="UNBESTIMMT" if abweichend or relevante else "ENTSCHIEDEN",
        fehlende_angaben=sorted(fehlend),
        entscheidungsrelevante_luecken=sorted(relevante),
        hinweise=hinweise,
        annahmen=[
            "Hochrisiko, Akteursbezug und Ausschluss Artikel 111 Absatz 1 qualifiziert",
            "Ereignisse betreffen denselben Typ und dasselbe Modell bis zum Stichtag",
        ],
        entscheidungsschritte=[
            dict(
                operation="HOCHRISIKO_BESTANDSWEG",
                bestandsgrenze=g,
                stichtag=stichtag,
                wert=k,
            )
            for g, k in zip(grenzen, kandidaten)
        ]
        + (
            [
                dict(
                    operation="OFFENE_RECHTSFRAGE",
                    frage_id="F004",
                    abweichende_felder=abweichend,
                )
            ]
            if abweichend
            else []
        ),
        nachweise=[
            dict(
                art="RECHTSQUELLE",
                fundstelle="ART_111/2",
                quellenfassung=quellenfassung,
            )
        ],
    )
    return ergebnis
