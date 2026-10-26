"""CE dimensions retain strict decimal input and separate duty from fulfillment."""

import pytest
from euaiact import pruefe_tatbestand, ermittle_pflicht


@pytest.mark.parametrize("value", [5, 5.0, 5.5, True])
def test_ce_height_requires_decimal_text(value):
    data = {"ce_hoehe_mm": value}
    result = pruefe_tatbestand(
        "CE_0765_ANH_II_3_HOEHE", data, quellenfassung="EUAIACT_2026_07_27"
    )
    assert result["status"] == "EINGABE_UNGUELTIG"
    assert type(data["ce_hoehe_mm"]) is type(value)
    assert data["ce_hoehe_mm"] == value
    assert type(result["eingaben"]["ce_hoehe_mm"]) is type(value)


def test_ce_duty_does_not_establish_fulfillment():
    result = ermittle_pflicht(
        "P_AIA_048_001",
        {"anbieterrolle": True, "hochrisikosystem": True},
        quellenfassung="EUAIACT_2026_07_27",
    )
    assert result["wert"]["ausloeser_erfuellt"] is True
    assert result["wert"]["erfuellung"] == "NICHT_GEPRUEFT"
    assert result["wert"]["erfuellungskriterien"] == ["AIA_048_001_KRITERIEN"]
