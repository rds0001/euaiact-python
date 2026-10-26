"""Lokale Periodenparameter, Vorlauf und Widerruf ausdrücklich verknüpfen."""

import pytest
from euaiact import berechne_frist, berechne_regel, ermittle_pflicht, pruefe_tatbestand

FASSUNG = "EUAIACT_2026_07_27"
KALENDER = {
    "von": "2024-01-01",
    "bis": "2036-12-31",
    "feiertage": [],
    "bezug": "SYNTHETISCH: keine Feiertage; keine reale Behördenkalenderfreigabe",
}


@pytest.mark.parametrize(
    "anker,ende,bericht,widerspruch",
    [
        ("2024-08-01", "2029-08-01", "2028-11-01", "2029-05-01"),
        ("2026-07-27", "2031-07-27", "2030-10-27", "2031-04-27"),
    ],
)
def test_zwei_kohorten_und_rueckwaerts_vorlauf(anker, ende, bericht, widerspruch):
    dauer = berechne_regel("AIA_097_002_DELEGATIONSDAUER", {}, quellenfassung=FASSUNG)
    termin = berechne_frist(
        anker,
        dauer["wert"]["anzahl"],
        dauer["wert"]["einheit"],
        modus="FESTER_TERMIN",
        quellenfassung=FASSUNG,
    )
    # Modus und ursprüngliche Kohorte ausdrücklich vorgegeben. Ein Datum allein
    # beweist weder fortbestehende Befugnis noch wirksame Verlängerung.
    assert termin["wert"] == ende
    for regel, erwartet in [
        ("AIA_097_002_BERICHTSVORLAUF", bericht),
        ("AIA_097_002_WIDERSPRUCHSVORLAUF", widerspruch),
    ]:
        vorlauf = berechne_regel(regel, {}, quellenfassung=FASSUNG)
        frist = berechne_frist(
            ende,
            vorlauf["wert"]["anzahl"],
            vorlauf["wert"]["einheit"],
            modus="RUECKWAERTS",
            kalender=KALENDER,
            quellenfassung=FASSUNG,
        )
        assert (
            frist["wert"] == erwartet
        )  # Sonntage werden rückwärts nicht nach vorn verschoben.


@pytest.mark.parametrize(
    "wirksam,erwartet", [(False, True), (True, False), (None, None)]
)
def test_periodendatum_ersetzt_keine_widerrufspruefung(wirksam, erwartet):
    daten = {
        "delegation_97_2_einschlaegig": True,
        "pruefzeitpunkt_liegt_in_wirksamer_delegationsperiode": True,
        "akteur_ist_europaeisches_parlament": True,
        "akteur_ist_rat": False,
        "widerrufsentscheidung_tatsaechlich_erlassen": True,
        "widerrufsentscheidung_erfasst_konkret_betrachtete_delegation": True,
        "widerrufsentscheidung_ist_zum_pruefzeitpunkt_wirksam": wirksam,
    }
    befugnis = pruefe_tatbestand("AIA_097_BEFUGNIS", daten, quellenfassung=FASSUNG)
    assert befugnis["wert"] is erwartet
    assert befugnis["anwendbarkeit"] == "UNBEKANNT"


def test_berichtspflicht_ist_keine_bestaetigte_erfuellung():
    pflicht = ermittle_pflicht(
        "P_AIA_097_002_BERICHT",
        {
            "betrachteter_akteur_ist_europaeische_kommission": True,
            "delegation_97_2_einschlaegig": True,
            "konkrete_delegationsperiode_ist_gegenstand_des_97_2_berichts": True,
        },
        quellenfassung=FASSUNG,
    )
    assert pflicht["wert"]["ausloeser_erfuellt"] is True
    assert pflicht["wert"]["erfuellung"] == "NICHT_GEPRUEFT"
    assert pflicht["wert"]["fristregel_ids"] == ["AIA_097_002_BERICHTSVORLAUF"]
