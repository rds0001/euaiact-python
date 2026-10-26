"""Öffentlicher Austauschvertrag für alle Katalogregeln und Fehlerumschläge."""

import json
from pathlib import Path
import pytest
from jsonschema import Draft202012Validator
from euaiact import (
    schema_info,
    regel_katalog,
    regel_info,
    pruefe_tatbestand,
    berechne_regel,
    berechne_frist,
    pruefe_anwendungsbeginn,
)

PRUEFER = Draft202012Validator(
    schema_info(), format_checker=Draft202012Validator.FORMAT_CHECKER
)


@pytest.mark.parametrize("regel", regel_katalog(), ids=lambda r: r["regel_id"])
def test_jede_katalogregel_hat_stabilen_umschlag(regel):
    funktion = (
        pruefe_tatbestand
        if "ausdruck" in regel_info(regel["regel_id"])
        else berechne_regel
    )
    PRUEFER.validate(
        funktion(regel["regel_id"], {}, quellenfassung=regel["quellenfassung"])
    )


def test_referenzwerte_passen_zum_ergebnistyp():
    pfad = Path(__file__).parent / "fixtures"
    for name in ("grundregeln", "rechenregeln"):
        daten = json.loads((pfad / f"{name}_referenzen.json").read_text())
        funktion = pruefe_tatbestand if name == "grundregeln" else berechne_regel
        for fall in daten["faelle"]:
            PRUEFER.validate(
                funktion(
                    fall["regel_id"],
                    fall["eingaben"],
                    quellenfassung=daten["quellenfassung"],
                )
            )


def test_schema_lokal_und_kopie_unabhaengig():
    schema = schema_info()
    Draft202012Validator.check_schema(schema)
    schema["required"].clear()
    assert schema_info()["required"]
    with pytest.raises(KeyError):
        schema_info("https://example.test/schema")


def test_fehler_metadaten_und_zeitumschlaege():
    PRUEFER.validate(pruefe_tatbestand(42, {}, quellenfassung={}))
    PRUEFER.validate(
        berechne_frist(
            "2026-10-23",
            2,
            "TAG",
            modus="FESTER_TERMIN",
            quellenfassung="EUAIACT_2026_07_27",
        )
    )
    PRUEFER.validate(
        pruefe_anwendungsbeginn(
            "ARTIKEL_101", "2026-10-24", quellenfassung="EUAIACT_2026_07_27"
        )
    )


@pytest.mark.parametrize("eingaben", [[True], {1: True}, None])
def test_fehlerhafte_native_objektform_bleibt_json_objekt(eingaben):
    ergebnis = pruefe_tatbestand(
        "AIA_051_002", eingaben, quellenfassung="EUAIACT_2026_07_27"
    )
    assert ergebnis["status"] == "EINGABE_UNGUELTIG"
    assert ergebnis["eingaben"] == {}
    PRUEFER.validate(ergebnis)
