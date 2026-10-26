"""Vorfall-Dauerparameter mit explizitem Kalender komponieren, ohne Sofortpflicht aufzuheben."""

from euaiact import berechne_frist, berechne_regel

FASSUNG = "EUAIACT_2026_07_27"
KALENDER = {
    "von": "2026-10-01",
    "bis": "2026-11-30",
    "feiertage": [],
    "bezug": "SYNTHETISCH: explizit keine Feiertage",
}


def test_behoerdenfrist_ab_empfang_mit_dauerparameter():
    dauer = berechne_regel("AIA_073_008_BEHOERDENDAUER", {}, quellenfassung=FASSUNG)
    assert dauer["status"] == "AUSGEWERTET"
    ende = berechne_frist(
        "2026-10-23",
        dauer["wert"]["anzahl"],
        dauer["wert"]["einheit"],
        modus="FRIST",
        kalender=KALENDER,
        quellenfassung=FASSUNG,
    )
    assert ende["wert"] == "2026-10-30"
    assert ende["anwendbarkeit"] == "UNBEKANNT"


def test_zweitagesdauer_im_expliziten_allgemeinen_fristmodus():
    dauer = berechne_regel(
        "AIA_073_MELDEFRISTTAGE",
        {
            "weitverbreiteter_verstoss": True,
            "schwere_irreversible_kritische_infrastrukturstoerung": None,
            "todesfall": None,
        },
        quellenfassung=FASSUNG,
    )
    assert dauer["wert"] == 2
    ende = berechne_frist(
        "2026-10-23",
        dauer["wert"],
        "TAG",
        modus="FRIST",
        kalender=KALENDER,
        quellenfassung=FASSUNG,
    )
    # Freitag ist Ereignistag; mindestens zwei Arbeitstage Montag und Dienstag.
    # Dies ist nur das äußerste Datum im gewählten allgemeinen Regime, keine Warteerlaubnis.
    assert ende["wert"] == "2026-10-27"


def test_dauerparameter_ersetzt_keinen_kalendernachweis():
    dauer = berechne_regel("AIA_073_008_BEHOERDENDAUER", {}, quellenfassung=FASSUNG)
    ende = berechne_frist(
        "2026-10-23",
        dauer["wert"]["anzahl"],
        "TAG",
        modus="FRIST",
        quellenfassung=FASSUNG,
    )
    assert ende["status"] == "EINGABE_FEHLT"
    assert ende["wert"] is None
