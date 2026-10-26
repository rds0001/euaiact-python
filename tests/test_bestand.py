"""Fachlich vor Implementierung festgelegte Bestands- und Grenztagsreferenzen."""

from copy import deepcopy
import json
from pathlib import Path
import pytest
from jsonschema import Draft202012Validator
from euaiact import pruefe_bestandsfrist, schema_info

FAELLE = json.loads(
    (Path(__file__).parent / "fixtures/bestandsfristen_referenzen.json").read_text()
)["faelle"]


@pytest.mark.parametrize("fall", FAELLE, ids=lambda f: f["fall_id"])
def test_bestandsreferenz(fall):
    vorher = deepcopy(fall["eingaben"])
    ergebnis = pruefe_bestandsfrist(**fall["eingaben"])
    for feld, wert in fall["erwartung"].items():
        assert ergebnis[feld] == wert, fall["herleitung"]
    Draft202012Validator(schema_info()).validate(ergebnis)
    assert fall["eingaben"] == vorher


def test_altbestand_entscheidet_trotz_zweiter_luecke():
    ergebnis = pruefe_bestandsfrist(**FAELLE[6]["eingaben"])
    assert ergebnis["fehlende_angaben"] == ["ereignisse.inverkehrbringen.erfolgt"]
    assert ergebnis["entscheidungsrelevante_luecken"] == []
