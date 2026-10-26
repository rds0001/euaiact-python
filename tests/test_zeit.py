"""Unabhängige Datumsgrenzen aus dem spezifizierten Fassungsvergleich."""

import json
from pathlib import Path
import pytest
from euaiact import pruefe_anwendungsbeginn

FAELLE = json.loads(
    (Path(__file__).parent / "fixtures/anwendungsbeginn_referenzen.json").read_text()
)["faelle"]


@pytest.mark.parametrize("fall", FAELLE, ids=lambda f: f["fall_id"])
def test_zeitreferenz(fall):
    ergebnis = pruefe_anwendungsbeginn(**fall["eingaben"])
    for feld, wert in fall["erwartung"].items():
        assert ergebnis[feld] == wert, fall["herleitung"]
    if ergebnis["status"] == "AUSGEWERTET":
        assert ergebnis["anwendbarkeit"] == "UNBEKANNT"
