"""Unabhängig hergeleitete Fachreferenzen und technische Kernverträge."""

from copy import deepcopy
import json
from pathlib import Path

import pytest

from euaiact import pruefe_stapel, pruefe_tatbestand, regel_info, eingabevertrag

REFERENZEN = json.loads(
    (Path(__file__).parent / "fixtures/grundregeln_referenzen.json").read_text()
)
FASSUNG = REFERENZEN["quellenfassung"]


@pytest.mark.parametrize("fall", REFERENZEN["faelle"], ids=lambda fall: fall["fall_id"])
def test_unabhaengige_referenz(fall):
    eingaben = deepcopy(fall["eingaben"])
    ergebnis = pruefe_tatbestand(fall["regel_id"], eingaben, quellenfassung=FASSUNG)
    assert ergebnis["wert"] is fall["erwartung"]["wert"], fall["herleitung"]
    assert ergebnis["status"] == fall["erwartung"]["status"]
    assert eingaben == fall["eingaben"]
    json.dumps(ergebnis, allow_nan=False)


def test_nicht_entscheidende_luecke():
    ergebnis = pruefe_tatbestand(
        "AIA_053_002",
        {"gpai_modell_mit_systemischem_risiko": True},
        quellenfassung=FASSUNG,
    )
    assert ergebnis["fehlende_angaben"]
    assert ergebnis["entscheidungsrelevante_luecken"] == []
    assert ergebnis["anwendbarkeit"] == "UNBEKANNT"


def test_katalogkopie_isoliert():
    info = regel_info("AIA_051_002")
    info["ausdruck"]["argumente"][1]["dezimal"] = "1"
    assert (
        pruefe_tatbestand(
            "AIA_051_002", {"trainings_flops": "2"}, quellenfassung=FASSUNG
        )["wert"]
        is False
    )


def test_transitiver_vertrag_und_cache_isoliert():
    vertrag = eingabevertrag("AIA_053_001_A")
    assert "gewichte_oeffentlich" in vertrag["felder"]
    assert "anbieterrolle" in vertrag["felder"]
    vertrag["felder"]["gewichte_oeffentlich"]["typ"] = "VERAENDERT"
    assert (
        eingabevertrag("AIA_053_001_A")["felder"]["gewichte_oeffentlich"]["typ"]
        == "BOOLEAN"
    )


def test_blattregel_hat_entscheidungsschritt():
    ergebnis = pruefe_tatbestand("AIA_ANH_III_4_A", {}, quellenfassung=FASSUNG)
    assert ergebnis["entscheidungsschritte"][-1]["operator"] == "REGELERGEBNIS"


def test_stabile_bedingungsadressen_und_originalwert():
    ergebnis = pruefe_tatbestand(
        "AIA_051_002",
        {"trainings_flops": "10000000000000000000000001"},
        quellenfassung=FASSUNG,
    )
    assert ergebnis["entscheidungsschritte"][0]["bedingung_id"] == "AIA_051_002:K0.0"
    assert ergebnis["entscheidungsschritte"][0]["wert"] == "10000000000000000000000001"
    assert ergebnis["entscheidungsschritte"][1]["bedingung_id"] == "AIA_051_002:K0"


def test_stapel_isoliert_ungueltige_fakten():
    faelle = [
        {
            "fall_id": "gueltig",
            "regel_id": "AIA_051_002",
            "eingaben": {"trainings_flops": "0"},
        },
        {
            "fall_id": "ungueltig",
            "regel_id": "AIA_051_002",
            "eingaben": {"trainings_flops": 1},
        },
    ]
    ergebnisse = pruefe_stapel(faelle, quellenfassung=FASSUNG)
    assert [r["fall_id"] for r in ergebnisse] == ["gueltig", "ungueltig"]
    assert [r["ergebnis"]["status"] for r in ergebnisse] == [
        "AUSGEWERTET",
        "EINGABE_UNGUELTIG",
    ]
    with pytest.raises(ValueError):
        pruefe_stapel([faelle[0], faelle[0]], quellenfassung=FASSUNG)


def test_quellenfassung_nicht_heimlich_ersetzen():
    ergebnis = pruefe_tatbestand("AIA_051_002", {}, quellenfassung="EUAIACT_2024_08_01")
    assert ergebnis["status"] == "EINGABE_UNGUELTIG"
    assert ergebnis["quellenfassung"] == "EUAIACT_2024_08_01"
