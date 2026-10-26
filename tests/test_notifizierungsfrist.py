"""Fachliche Komposition von Einwandsperiode und explizitem lokalen Kalender."""

import pytest
from euaiact import berechne_regel, berechne_frist


@pytest.mark.parametrize(
    "grundlage, ende",
    [
        ("AKKREDITIERUNGSBESCHEINIGUNG", "2026-11-09"),
        ("DOKUMENTENNACHWEISE", "2026-12-23"),
    ],
)
def test_notifizierungsfrist_mit_eigenem_kalender(grundlage, ende):
    fassung = "EUAIACT_2026_07_27"
    periode = berechne_regel(
        "AIA_030_EINWANDSPERIODE",
        {"notifizierungsgrundlage": grundlage},
        quellenfassung=fassung,
    )
    assert periode["status"] == "AUSGEWERTET"
    ergebnis = berechne_frist(
        "2026-10-23",
        **periode["wert"],
        modus="FRIST",
        kalender={
            "von": "2026-10-01",
            "bis": "2027-01-31",
            "feiertage": ["2026-11-06"],
            "bezug": "SYNTHETISCHER_FEIERTAG",
        },
        quellenfassung=fassung,
    )
    assert ergebnis["status"] == "AUSGEWERTET"
    assert ergebnis["wert"] == ende
