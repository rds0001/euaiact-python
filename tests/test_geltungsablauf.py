"""Cross-stage expectations keep applicability, transition and fulfilment apart."""

import importlib.util
import json
from pathlib import Path
from copy import deepcopy
import pytest

EXAMPLES = Path(__file__).parents[1] / "examples"
spec = importlib.util.spec_from_file_location(
    "geltungsablauf", EXAMPLES / "geltungsablauf.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
CASES = json.loads((EXAMPLES / "geltungsablaeufe.json").read_text())["faelle"]


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["fall_id"])
def test_geltungsablauf(case):
    before = deepcopy(case)
    actual = module.auswerten(dict(faelle=[case]))[0]
    assert case == before
    for stage, step in zip(actual["schritte"], case["schritte"]):
        for key, value in step["erwartung"].items():
            assert stage["ergebnis"][key] == value, case["herleitung"]
        assert stage["ergebnis"]["anwendbarkeit"] == "UNBEKANNT"


def test_abweichender_zeitbezug_wird_nicht_stillschweigend_uebernommen():
    case = deepcopy(CASES[0])
    case["schritte"][2]["parameter"]["stichtag"] = "2029-01-01"
    with pytest.raises(ValueError, match="gemeinsamen Kontext"):
        module.auswerten(dict(faelle=[case]))
