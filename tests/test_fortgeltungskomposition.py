"""Unterschiedliche Ereignisanker und Bewertungserfüllung getrennt prüfen."""

import pytest
from euaiact import berechne_regel, berechne_frist, ermittle_pflicht, pruefe_tatbestand

FASSUNG = "EUAIACT_2026_07_27"


@pytest.mark.parametrize(
    "regel,anker,ende",
    [
        ("AIA_036_003_FORTGELTUNG", "2026-01-31", "2026-10-31"),
        ("AIA_036_009_GRUNDFORTGELTUNG", "2026-02-28", "2026-11-28"),
        ("AIA_036_009_BEWERTUNGSDAUER", "2026-02-28", "2027-02-28"),
        ("AIA_036_008_B_UEBERNAHMEDAUER", "2026-01-31", "2026-04-30"),
    ],
)
def test_ausdrueckliche_kalenderanker(regel, anker, ende):
    # Expliziter Kalendervergleich, keine automatische Wahl des Fristregimes.
    dauer = berechne_regel(regel, {}, quellenfassung=FASSUNG)["wert"]
    ergebnis = berechne_frist(
        anker,
        dauer["anzahl"],
        dauer["einheit"],
        modus="FESTER_TERMIN",
        quellenfassung=FASSUNG,
    )
    assert ergebnis["wert"] == ende
    assert ergebnis["anwendbarkeit"] == "UNBEKANNT"


def test_laufende_bewertungsfrist_ist_keine_abgeschlossene_bewertung():
    pflicht = ermittle_pflicht(
        "P_AIA_036_009_BEWERTUNG",
        {
            "stelle_hat_sofortige_verantwortung_nach_benennungswiderruf_schriftlich_uebernommen": True
        },
        quellenfassung=FASSUNG,
    )
    daten = {
        "bewertung_durch_uebernehmende_stelle_innerhalb_zwoelf_monaten_abgeschlossen": False
    }
    verlauf = pruefe_tatbestand(
        "AIA_036_009_BEWERTUNGSVERLAUF",
        daten
        | {"zwoelfmonatsbewertungsfrist_nach_benennungswiderruf_abgelaufen": False},
        quellenfassung=FASSUNG,
    )
    erfuellung = pruefe_tatbestand(
        "AIA_036_009_BEWERTUNG_KRITERIEN", daten, quellenfassung=FASSUNG
    )
    assert pflicht["wert"]["ausloeser_erfuellt"] is True
    assert pflicht["wert"]["erfuellung"] == "NICHT_GEPRUEFT"
    assert pflicht["wert"]["fristregel_ids"] == ["AIA_036_009_BEWERTUNGSDAUER"]
    assert verlauf["wert"] is True
    assert erfuellung["wert"] is False
