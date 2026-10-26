"""Dauerparameter im ausdrücklich gewählten allgemeinen Fristmodus verknüpfen."""

import pytest
from euaiact import berechne_frist, berechne_regel, ermittle_pflicht, pruefe_tatbestand

FASSUNG = "EUAIACT_2026_07_27"
KALENDER = {
    "von": "2026-01-01",
    "bis": "2038-12-31",
    "feiertage": [],
    "bezug": "SYNTHETISCH: ausdrücklich keine Feiertage im gesamten Zeitraum",
}
FAELLE = [
    ("AIA_018_AUFBEWAHRUNGSDAUER", "2028-02-29", "2038-03-01"),
    ("AIA_022_003_B_AUFBEWAHRUNGSDAUER", "2028-02-29", "2038-03-01"),
    ("AIA_023_005_AUFBEWAHRUNGSDAUER", "2028-02-29", "2038-03-01"),
    ("AIA_019_001_REGELMINDESTDAUER", "2026-08-31", "2027-03-01"),
    ("AIA_026_006_REGELMINDESTDAUER", "2026-08-31", "2027-03-01"),
]


@pytest.mark.parametrize("regel,ereignis,erwartet", FAELLE)
def test_dauer_mit_explizitem_fristmodus(regel, ereignis, erwartet):
    dauer = berechne_regel(regel, {}, quellenfassung=FASSUNG)
    ende = berechne_frist(
        ereignis,
        dauer["wert"]["anzahl"],
        dauer["wert"]["einheit"],
        modus="FRIST",
        kalender=KALENDER,
        quellenfassung=FASSUNG,
    )
    # Fehlender Korrespondenztag -> Februarende; Sonntag -> Montag.
    # Der Aufrufer wählt und qualifiziert Zeitanker/Regime ausdrücklich.
    assert ende["status"] == "AUSGEWERTET"
    assert ende["wert"] == erwartet
    assert ende["anwendbarkeit"] == "UNBEKANNT"


def test_zehnjahresparameter_ersetzt_keine_kalenderdeckung():
    dauer = berechne_regel("AIA_018_AUFBEWAHRUNGSDAUER", {}, quellenfassung=FASSUNG)
    for kalender in (None, KALENDER | {"bis": "2038-02-28"}):
        ende = berechne_frist(
            "2028-02-29",
            dauer["wert"]["anzahl"],
            dauer["wert"]["einheit"],
            modus="FRIST",
            kalender=kalender,
            quellenfassung=FASSUNG,
        )
        assert ende["status"] == "EINGABE_FEHLT"
        assert ende["wert"] is None


def test_regelmindestdauer_ist_keine_erfuellungs_oder_loeschfreigabe():
    pflicht = ermittle_pflicht(
        "P_AIA_026_006",
        {
            "betreiberrolle": True,
            "hochrisikosystem": True,
            "automatisch_erzeugte_protokolle_unter_eigener_kontrolle": True,
        },
        quellenfassung=FASSUNG,
    )
    assert pflicht["wert"]["ausloeser_erfuellt"] is True
    assert pflicht["wert"]["erfuellung"] == "NICHT_GEPRUEFT"
    assert pflicht["wert"]["fristregel_ids"] == ["AIA_026_006_REGELMINDESTDAUER"]
    offen = pruefe_tatbestand(
        "AIA_PROTOKOLL_AUFBEWAHRUNGSKRITERIEN",
        {"sechsmonatsmindestdauer_der_protokollaufbewahrung_eingehalten": True},
        quellenfassung=FASSUNG,
    )
    assert offen["status"] == "EINGABE_FEHLT"
    assert offen["wert"] is None
