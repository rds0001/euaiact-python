"""Dieselben Regeln über unterschiedliche lokale Unternehmenszuordnungen."""

import importlib.util
from pathlib import Path


def test_synthetische_unternehmen():
    verzeichnis = Path(__file__).resolve().parents[1] / "examples"
    spezifikation = importlib.util.spec_from_file_location(
        "unternehmen_beispiel", verzeichnis / "unternehmen.py"
    )
    modul = importlib.util.module_from_spec(spezifikation)
    spezifikation.loader.exec_module(modul)
    ergebnisse = modul.auswerten(verzeichnis / "unternehmen_synthetisch.json")
    assert len(ergebnisse) == 31
    assert len({e["szenario_id"] for e in ergebnisse}) == 8

    index = {e["fall_id"]: e["ergebnis"] for e in ergebnisse}
    assert index["gpai_stellungnahmeseiten"]["wert"] == 50
    assert index["gpai_widerspruechliche_seiten"]["status"] == "EINGABE_UNGUELTIG"
    assert index["gpai_beleguebersetzung_offen"]["status"] == "EINGABE_FEHLT"
    assert index["gpai_digitaler_empfang"]["wert"] is True
    assert index["gpai_empfang_bestaetigung_ausstehend"]["wert"] is False

    assert index["transparenz_rechtzeitig"]["wert"] is True
    assert index["transparenz_verspaetet"]["wert"] is False
    assert index["transparenz_offen"]["status"] == "EINGABE_FEHLT"

    assert index["jae_halb_halb"]["wert"] == "0.25"
    assert index["jae_abschnitt_offen"]["status"] == "EINGABE_FEHLT"
    assert index["jae_disjunkte_summe"]["wert"] == "0.75"

    assert index["geltung_open_source"]["wert"] is False
    assert index["geltung_open_source_transparenz"]["wert"] is True
    assert index["geltung_realtest"]["wert"] is True
    assert index["geltung_reine_forschung"]["wert"] is False
    assert index["geltung_system_offen"]["status"] == "EINGABE_FEHLT"

    assert index["jae_rational_1"]["wert"] == {"zaehler": "1", "nenner": "6"}
    assert index["jae_rational_2"]["wert"] == {"zaehler": "1", "nenner": "2"}
    assert index["jae_rational_3"]["wert"]["smc_groessenrahmen"] is True
