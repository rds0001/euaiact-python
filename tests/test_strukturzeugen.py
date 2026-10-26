"""Bounded structural witnesses; separate from independent legal references."""

import json
from copy import deepcopy
from pathlib import Path
import pytest
from euaiact import pruefe_tatbestand

REFERENZEN = json.loads(
    (Path(__file__).parent / "fixtures/strukturreferenzen.json").read_text()
)


@pytest.mark.parametrize("fall", REFERENZEN["faelle"], ids=lambda f: f["fall_id"])
def test_strukturzeuge(fall):
    daten = deepcopy(fall["eingaben"])
    result = pruefe_tatbestand(
        fall["regel_id"], daten, quellenfassung=REFERENZEN["quellenfassung"]
    )
    assert result["wert"] is fall["erwartung"]["wert"]
    assert result["status"] == fall["erwartung"]["status"]
    assert daten == fall["eingaben"]
    targets = {
        s["bedingung_id"] + ":" + str(s["wert"])
        for s in result["entscheidungsschritte"]
        if "bedingung_id" in s
    }
    assert set(fall["ziel_ids"]) <= targets


@pytest.mark.parametrize(
    "op,rid,path,fields,expected",
    [
        (
            "UND",
            "AIA_003_004",
            "0.1.0",
            ["natuerliche_person", "rein_persoenlich_nicht_beruflich"],
            [True, False, None, False, False, False, None, False, None],
        ),
        (
            "ODER",
            "AIA_003_003",
            "0.0",
            ["entwickelt_selbst", "laesst_entwickeln"],
            [True, True, True, True, False, None, True, None, None],
        ),
        (
            "NICHT",
            "AIA_003_023",
            "0.1",
            ["bei_urspruenglicher_bewertung_vorgesehen"],
            [False, True, None],
        ),
    ],
)
def test_vollstaendige_grundoperatoren(op, rid, path, fields, expected):
    from itertools import product

    for values, value in zip(
        product([True, False, None], repeat=len(fields)), expected
    ):
        result = pruefe_tatbestand(
            rid, dict(zip(fields, values)), quellenfassung=REFERENZEN["quellenfassung"]
        )
        steps = [
            s
            for s in result["entscheidungsschritte"]
            if s.get("bedingung_id") == rid + ":K" + path
        ]
        assert len(steps) == 1 and steps[0]["wert"] is value
