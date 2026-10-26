"""Explizite lokale GPAI-Status-/Pflichtkomposition ohne globale Konformitätszusage."""

import pytest
from euaiact import ermittle_pflicht, pruefe_tatbestand

FASSUNG = "EUAIACT_2026_07_27"


def einstufung(flop="10000000000000000000000001", ausnahme=False, entscheidung=False):
    return pruefe_tatbestand(
        "AIA_051_SYSTEMRISIKOEINSTUFUNG",
        {
            "gpai_modell": True,
            "hohe_wirkmaechtigkeit_durch_geeignete_werkzeuge_und_methoden_bewertet": False,
            "trainings_flops": flop,
            "kommission_hat_gleichwertige_faehigkeiten_oder_auswirkungen_festgestellt": entscheidung,
            "kommissionsentscheidung_beruecksichtigt_anhang_xiii": True,
            "wirksame_kommissionsausnahmeentscheidung_zum_51_1_a_weg": ausnahme,
        },
        quellenfassung=FASSUNG,
    )


@pytest.mark.parametrize(
    "flop,ausnahme,entscheidung,erwartet",
    [
        ("10000000000000000000000001", False, False, True),
        ("10000000000000000000000001", True, False, False),
        ("10000000000000000000000001", None, False, None),
        ("10000000000000000000000000", False, False, False),
        ("0", True, True, True),
    ],
)
def test_status_explizit_an_systemrisikopflicht_uebergeben(
    flop, ausnahme, entscheidung, erwartet
):
    status = einstufung(flop, ausnahme, entscheidung)
    assert status["wert"] is erwartet
    pflicht = ermittle_pflicht(
        "P_AIA_055_001_A",
        {"anbieterrolle": True, "gpai_modell_mit_systemischem_risiko": status["wert"]},
        quellenfassung=FASSUNG,
    )
    assert pflicht["wert"]["ausloeser_erfuellt"] is erwartet
    assert pflicht["wert"]["erfuellung"] == "NICHT_GEPRUEFT"
    assert pflicht["anwendbarkeit"] == "UNBEKANNT"
    assert pflicht["status"] == ("EINGABE_FEHLT" if erwartet is None else "AUSGEWERTET")


@pytest.mark.parametrize("systemisch", [False, True])
def test_open_source_nur_dokumentation_und_nicht_urheberrecht(systemisch):
    daten = {
        "anbieterrolle": True,
        "gpai_modell": True,
        "lizenz_erlaubt_zugang_nutzung_aenderung_verbreitung": True,
        "gewichte_oeffentlich": True,
        "architekturinformation_oeffentlich": True,
        "nutzungsinformation_oeffentlich": True,
        "gpai_modell_mit_systemischem_risiko": systemisch,
    }
    dokumentation = ermittle_pflicht("P_AIA_053_001_A", daten, quellenfassung=FASSUNG)
    # Für jede Regel ihren eigenen Eingabevertrag verwenden; keine fremden Felder.
    urheberrecht = ermittle_pflicht(
        "P_AIA_053_001_C",
        {"anbieterrolle": True, "gpai_modell": True},
        quellenfassung=FASSUNG,
    )
    assert dokumentation["wert"]["ausloeser_erfuellt"] is systemisch
    assert urheberrecht["wert"]["ausloeser_erfuellt"] is True
    assert urheberrecht["wert"]["erfuellung"] == "NICHT_GEPRUEFT"


def test_bekannte_kuenftige_wirkmaechtigkeit_meldet_ohne_heutigen_statuswechsel():
    status = einstufung("0", False, False)
    assert status["wert"] is False
    meldung = ermittle_pflicht(
        "P_AIA_052_001_MELDUNG",
        {
            "anbieterrolle": True,
            "gpai_modell": True,
            "hohe_wirkmaechtigkeit_durch_geeignete_werkzeuge_und_methoden_bewertet": False,
            "trainings_flops": "0",
            "bekannt_dass_hohe_wirkmaechtigkeit_erreicht_werden_wird": True,
        },
        quellenfassung=FASSUNG,
    )
    assert meldung["wert"]["ausloeser_erfuellt"] is True
    assert meldung["wert"]["erfuellung"] == "NICHT_GEPRUEFT"
