"""Native integer-value interoperability without relaxing exact text contracts."""

import json
import pytest
from euaiact import (
    berechne_regel,
    berechne_frist,
    pruefe_tatbestand,
    schreibe_json,
    lese_json,
)

F = "EUAIACT_2026_07_27"


def test_native_ganzzahlwerte_werden_kanonisch_ohne_mutation_verarbeitet():
    data = {"mitgliederzahl": 60.0}
    result = berechne_regel("PANEL_EU_MINDESTZAHL", data, quellenfassung=F)
    assert result == berechne_regel(
        "PANEL_EU_MINDESTZAHL", {"mitgliederzahl": 60}, quellenfassung=F
    )
    assert result["wert"] == 48 and type(result["wert"]) is int
    assert type(data["mitgliederzahl"]) is float
    assert pruefe_tatbestand(
        "DVO_0454_003_002_GROESSENGRENZE",
        {"anzahl_bestellter_panel_experten": 60.0},
        quellenfassung=F,
    ) == pruefe_tatbestand(
        "DVO_0454_003_002_GROESSENGRENZE",
        {"anzahl_bestellter_panel_experten": 60},
        quellenfassung=F,
    )


@pytest.mark.parametrize(
    "value",
    [True, "5", 5.5, float("inf"), float("nan"), 9007199254740992, complex(5, 0)],
)
def test_andere_typen_werden_nicht_zu_ganzzahlen_umgedeutet(value):
    assert (
        berechne_regel(
            "PANEL_EU_MINDESTZAHL", {"mitgliederzahl": value}, quellenfassung=F
        )["status"]
        == "EINGABE_UNGUELTIG"
    )
    assert (
        berechne_frist(
            "2026-01-01", value, "MONAT", modus="FESTER_TERMIN", quellenfassung=F
        )["status"]
        == "EINGABE_UNGUELTIG"
    )
    assert (
        berechne_frist(
            "2026-01-01T12:30:00Z", value, "STUNDE", modus="FRIST", quellenfassung=F
        )["status"]
        == "EINGABE_UNGUELTIG"
    )


@pytest.mark.parametrize(
    "unit,start", [("MONAT", "2026-01-31"), ("STUNDE", "2026-01-01T12:30:00Z")]
)
def test_ganzzahliger_float_als_zeitanzahl(unit, start):
    mode = "FRIST" if unit == "STUNDE" else "FESTER_TERMIN"
    a = berechne_frist(start, 1.0, unit, modus=mode, quellenfassung=F)
    b = berechne_frist(start, 1, unit, modus=mode, quellenfassung=F)
    assert a == b and a["status"] == "AUSGEWERTET"
    assert type(a["eingaben"]["anzahl"]) is int


def test_exakte_dezimaltexte_bleiben_strikt():
    a = berechne_regel(
        "AIA_075C_005_TAGESEINKOMMEN",
        {"qualifiziertes_durchschnittliches_tageseinkommen_eur": 5.0},
        quellenfassung=F,
    )
    assert a["status"] == "EINGABE_UNGUELTIG"


def test_json_austausch_bleibt_kanonisch(tmp_path):
    path = tmp_path / "local.json"
    # Native integral floats can be written canonically, but a lexical JSON
    # decimal remains outside the documented portable-number contract.
    schreibe_json({"anzahl": 5.0}, path)
    assert lese_json(path) == {"anzahl": 5}
    assert "5.0" not in path.read_text()
    path.write_text(json.dumps({"anzahl": 5.0}))
    with pytest.raises(ValueError):
        lese_json(path)
