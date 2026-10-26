"""Mengen müssen im Schema, Ergebnis und lokalen Datenaustausch gleich bleiben."""

from copy import deepcopy

import pytest
from jsonschema import Draft202012Validator
from euaiact import eingabevertrag, pruefe_tatbestand, schema_info

ID = "AIA_049_004_DATEN_A"
FELD = "registrierte_angaben_a"
FASSUNG = "EUAIACT_2026_07_27"


@pytest.mark.parametrize(
    "wert,gueltig",
    [
        ([], True),
        (["10", "1"], True),
        (None, True),
        (["1", "1"], False),
        ({}, False),
        ("1", False),
        ([None], False),
        ([True], False),
        ([["1"]], False),
        (["999"], False),
    ],
)
def test_schema_und_native_validierung(wert, gueltig):
    daten = {FELD: wert}
    assert (
        Draft202012Validator(schema_info(ID + ":EINGABEN")).is_valid(daten) is gueltig
    )
    ergebnis = pruefe_tatbestand(ID, daten, quellenfassung=FASSUNG)
    assert (ergebnis["status"] != "EINGABE_UNGUELTIG") is gueltig


def test_reihenfolge_originalwerte_und_isolierter_vertrag():
    daten = {FELD: ["10", "3", "1"]}
    original = deepcopy(daten)
    ergebnis = pruefe_tatbestand(ID, daten, quellenfassung=FASSUNG)
    assert ergebnis["wert"] is True
    assert ergebnis["eingaben"] == original == daten
    assert ergebnis["entscheidungsschritte"][0]["wert"] == original[FELD]
    assert ergebnis["entscheidungsschritte"][1]["operator"] == "TEILMENGE"
    vertrag = eingabevertrag(ID)
    vertrag["felder"][FELD]["werte"].append("999")
    assert "999" not in eingabevertrag(ID)["felder"][FELD]["werte"]
