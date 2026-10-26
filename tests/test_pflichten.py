"""Pflichtauslösung ist von Erfüllung und allgemeiner Anwendbarkeit getrennt."""

from copy import deepcopy
import json
from pathlib import Path
import pytest
from jsonschema import Draft202012Validator
from euaiact import ermittle_pflicht, pflicht_katalog, regel_info, schema_info

DATEN = json.loads(
    (Path(__file__).parent / "fixtures/pflichten_referenzen.json").read_text()
)


@pytest.mark.parametrize("fall", DATEN["faelle"], ids=lambda f: f["fall_id"])
def test_pflichtreferenz(fall):
    vorher = deepcopy(fall["eingaben"])
    ergebnis = ermittle_pflicht(
        fall["pflicht_id"], fall["eingaben"], quellenfassung=DATEN["quellenfassung"]
    )
    assert ergebnis["status"] == fall["status"], fall["herleitung"]
    if fall["status"] == "EINGABE_UNGUELTIG":
        assert ergebnis["wert"] is None
    else:
        assert ergebnis["wert"]["ausloeser_erfuellt"] == fall["ausloeser_erfuellt"], (
            fall["herleitung"]
        )
        assert ergebnis["wert"]["pflicht_id"] == fall["pflicht_id"]
        assert ergebnis["wert"]["erfuellung"] == "NICHT_GEPRUEFT"
        assert ergebnis["anwendbarkeit"] == "UNBEKANNT"
    Draft202012Validator(schema_info()).validate(ergebnis)
    assert fall["eingaben"] == vorher


def test_katalog_kopien_und_verweise():
    katalog = pflicht_katalog()
    assert len({p["pflicht_id"] for p in katalog}) == len(katalog)
    for pflicht in katalog:
        assert "ausdruck" in regel_info(pflicht["ausloeser_regel"])
        for regel in pflicht["erfuellungskriterien"]:
            assert "ausdruck" in regel_info(regel)
    katalog[0]["nachweisanforderungen"].clear()
    assert pflicht_katalog()[0]["nachweisanforderungen"]


def test_pflichtausgabe_behaelt_zeitregeln_und_gegenstand():
    fassung = DATEN["quellenfassung"]
    meldung = ermittle_pflicht("P_AIA_052_001_MELDUNG", {}, quellenfassung=fassung)
    assert meldung["wert"]["fristregel_ids"] == ["AIA_052_001_MELDEHOECHSTDAUER"]
    assert meldung["wert"]["gegenstand"]
    assert meldung["wert"]["fundstellen"] == ["ART_052/1"]
    transparenz = ermittle_pflicht(
        "P_AIA_050_001", {"anbieterrolle": False}, quellenfassung=fassung
    )
    assert transparenz["wert"]["ausloeser_erfuellt"] is False
    assert transparenz["wert"]["erfuellung"] == "NICHT_GEPRUEFT"
    assert transparenz["wert"]["fristregel_ids"] == [
        "AIA_050_005_INFORMATIONSZEITPUNKT"
    ]
    assert (
        regel_info(transparenz["wert"]["fristregel_ids"][0])["operation"]
        == "ZEITPUNKT_KLEINER_GLEICH"
    )
    # Ein ausgehändigter Katalog-/Ergebnisdatensatz darf spätere Aufrufe nicht verändern.
    transparenz["wert"]["fristregel_ids"].clear()
    assert ermittle_pflicht("P_AIA_050_001", {}, quellenfassung=fassung)["wert"][
        "fristregel_ids"
    ]
