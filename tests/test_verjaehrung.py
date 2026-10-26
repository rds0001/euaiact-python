"""Independent timeline expectations, including non-revival and open law."""

import json
from copy import deepcopy
from pathlib import Path
import pytest
from euaiact import berechne_verjaehrung, schema_info
from jsonschema import Draft202012Validator

VALIDATOR = Draft202012Validator(schema_info())

CASES = json.loads(
    (Path(__file__).parent / "fixtures/verjaehrung_referenzen.json").read_text()
)["faelle"]


@pytest.mark.parametrize("case", CASES, ids=lambda c: c["fall_id"])
def test_verjaehrungsverlauf(case):
    inputs = deepcopy(case["eingaben"])
    result = berechne_verjaehrung(**inputs)
    VALIDATOR.validate(result)
    expected = case["erwartung"]
    assert result["status"] == expected["status"], (case["herleitung"], result)
    if expected["wert"] is None:
        assert result["wert"] is None
    else:
        for key, value in expected["wert"].items():
            assert result["wert"][key] == value, (case["herleitung"], key, result)
    assert inputs == case["eingaben"]
    json.dumps(result, allow_nan=False)
