"""Independent composite-period examples, not implementation-derived oracles."""

import json
from pathlib import Path
from copy import deepcopy
import pytest
from jsonschema import Draft202012Validator
from euaiact import berechne_periodenfrist, schema_info

DATA = json.loads(
    (Path(__file__).parent / "fixtures/periodenfristen_referenzen.json").read_text()
)


@pytest.mark.parametrize("case", DATA["faelle"], ids=lambda c: c["fall_id"])
def test_periodenreferenz(case):
    inputs = deepcopy(case["eingaben"])
    result = berechne_periodenfrist(**inputs)
    assert result["wert"] == case["erwartung"]["wert"], case["herleitung"]
    assert result["status"] == case["erwartung"]["status"]
    assert inputs == case["eingaben"]
    Draft202012Validator(schema_info()).validate(result)
