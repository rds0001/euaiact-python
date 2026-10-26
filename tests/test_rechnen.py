"""Unabhängige Rechenreferenzen, ausdrücklich ohne gerundete Sollwerte."""

import json
from pathlib import Path

import pytest

from euaiact import berechne_regel, berechne_bussgeldobergrenze

FAELLE = json.loads(
    (Path(__file__).parent / "fixtures/rechenregeln_referenzen.json").read_text()
)["faelle"]
FASSUNG = "EUAIACT_2026_07_27"


@pytest.mark.parametrize("fall", FAELLE, ids=lambda f: f["fall_id"])
def test_rechenreferenz(fall):
    ergebnis = berechne_regel(
        fall["regel_id"], fall["eingaben"], quellenfassung=FASSUNG
    )
    assert ergebnis["wert"] == fall["wert"], fall["herleitung"]
    assert ergebnis["status"] == fall.get("status", "AUSGEWERTET")
    json.dumps(ergebnis, allow_nan=False)


def test_unbekannter_umsatz_ist_keine_null():
    ergebnis = berechne_bussgeldobergrenze(
        {"verstosskategorie": "PFLICHT", "akteurklasse": "KMU"}, quellenfassung=FASSUNG
    )
    assert ergebnis["wert"] is None
    assert ergebnis["status"] == "EINGABE_FEHLT"
    assert ergebnis["entscheidungsrelevante_luecken"] == [
        "weltweiter_vorjahresumsatz_eur"
    ]


def test_ungueltiger_irrelevanter_umsatz():
    ergebnis = berechne_bussgeldobergrenze(
        {
            "verstosskategorie": "PFLICHT",
            "akteurklasse": "KEIN_UNTERNEHMEN",
            "weltweiter_vorjahresumsatz_eur": "-1",
        },
        quellenfassung=FASSUNG,
    )
    assert ergebnis["status"] == "EINGABE_UNGUELTIG"


def test_groessenmerkmale_mit_teilweise_fehlenden_finanzdaten():
    ergebnis = berechne_regel(
        "KMU_SCHWELLEN",
        {"jahresarbeitseinheiten": "249", "jahresumsatz_eur": "50000000"},
        quellenfassung=FASSUNG,
    )
    assert ergebnis["wert"] == {
        "kleinst": False,
        "klein": False,
        "kmu": True,
        "smc_groessenrahmen": True,
    }
    assert ergebnis["status"] == "AUSGEWERTET"
    assert ergebnis["fehlende_angaben"] == ["jahresbilanzsumme_eur"]
    assert ergebnis["entscheidungsrelevante_luecken"] == []


def test_kuerzeste_meldefrist_hat_keine_entscheidende_restluecke():
    ergebnis = berechne_regel(
        "AIA_073_MELDEFRISTTAGE",
        {"weitverbreiteter_verstoss": True},
        quellenfassung=FASSUNG,
    )
    assert ergebnis["wert"] == 2
    assert ergebnis["fehlende_angaben"] == [
        "schwere_irreversible_kritische_infrastrukturstoerung",
        "todesfall",
    ]
    assert ergebnis["entscheidungsrelevante_luecken"] == []


def test_feste_dauer_ist_kopie_und_kein_verstecktes_datum():
    from euaiact import regel_info, eingabevertrag, schema_info

    kennung = "AIA_036_003_VORANKUENDIGUNG"
    ergebnis = berechne_regel(kennung, {}, quellenfassung=FASSUNG)
    assert ergebnis["wert"] == {"anzahl": 1, "einheit": "JAHR"}
    assert regel_info(kennung)["zeitrelation"] == "VOR"
    assert eingabevertrag(kennung)["felder"] == {}
    assert schema_info(kennung + ":EINGABEN")["properties"] == {}
    ergebnis["wert"]["anzahl"] = 99
    assert ergebnis["rechenschritte"][0]["wert"]["anzahl"] == 1
    assert berechne_regel(kennung, {}, quellenfassung=FASSUNG)["wert"]["anzahl"] == 1


def test_dauerauswahl_spur_und_kopie():
    kennung = "AIA_079_008_EINWANDSDAUER"
    eingaben = {"massnahmenanlass": "VERBOT_ARTIKEL_5"}
    ergebnis = berechne_regel(kennung, eingaben, quellenfassung=FASSUNG)
    assert ergebnis["rechenschritte"][0]["auswahl"] == "VERBOT_ARTIKEL_5"
    ergebnis["wert"]["anzahl"] = 999
    assert ergebnis["rechenschritte"][0]["wert"]["anzahl"] == 30
    assert (
        berechne_regel(kennung, eingaben, quellenfassung=FASSUNG)["wert"]["anzahl"]
        == 30
    )
