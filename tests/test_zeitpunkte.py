"""Zeitpunktvertrag: öffentliche API, Schema und unabhängige Umgebungswerte."""

from copy import deepcopy
from datetime import datetime, timezone
import os
import time

from jsonschema import Draft202012Validator
import pytest
from euaiact import berechne_regel, schema_info

ID = "AIA_050_005_INFORMATIONSZEITPUNKT"
FASSUNG = "EUAIACT_2026_07_27"


def test_spur_boolean_und_unveraenderte_eingaben():
    daten = {
        "transparenzinformation_zeitpunkt": "2026-10-25T12:00:00.000001+02:00",
        "erste_interaktion_oder_exposition_zeitpunkt": "2026-10-25T10:00:00Z",
    }
    vorher = deepcopy(daten)
    ergebnis = berechne_regel(ID, daten, quellenfassung=FASSUNG)
    assert ergebnis["wert"] is False
    assert ergebnis["ergebnistyp"] == "WAHRHEITSWERT"
    assert ergebnis["status"] == "AUSGEWERTET"
    assert ergebnis["rechenschritte"] == [
        {
            "operation": "ZEITPUNKT_KLEINER_GLEICH",
            "operanden": list(daten.values()),
            "vergleichsbasis": "UTC, Mikrosekunden exakt",
            "wert": False,
        }
    ]
    ergebnis["rechenschritte"][0]["operanden"][0] = "veraendert"
    assert daten == vorher


def test_schema_und_native_kalenderqualifikation():
    pruefer = Draft202012Validator(schema_info(ID + ":EINGABEN"))
    feld = "transparenzinformation_zeitpunkt"
    for wert in ["2026-01-01T00:00:00Z", "2026-01-01T00:00:00.123456+02:30", None]:
        assert pruefer.is_valid({feld: wert})
    for wert in [
        "2026-01-01",
        "2026-01-01T00:00:00",
        "2026-01-01T00:00:00Z\n",
        0,
        True,
    ]:
        assert not pruefer.is_valid({feld: wert})
    # Kalendersemantik wird nativ validiert, unabhängig von optionalen Schema-Formaten.
    assert (
        berechne_regel(ID, {feld: "1900-02-29T00:00:00Z"}, quellenfassung=FASSUNG)[
            "status"
        ]
        == "EINGABE_UNGUELTIG"
    )


@pytest.mark.parametrize(
    "wert", [datetime(2026, 1, 1, tzinfo=timezone.utc), [], {}, 1.5]
)
def test_keine_stille_objektkonvertierung(wert):
    assert (
        berechne_regel(
            ID, {"transparenzinformation_zeitpunkt": wert}, quellenfassung=FASSUNG
        )["status"]
        == "EINGABE_UNGUELTIG"
    )


def test_systemzeitzone_ohne_einfluss():
    daten = {
        "transparenzinformation_zeitpunkt": "2026-10-25T02:30:00+02:00",
        "erste_interaktion_oder_exposition_zeitpunkt": "2026-10-25T02:30:00+01:00",
    }
    original = os.environ.get("TZ")
    try:
        ergebnisse = []
        for zone in ["UTC", "Pacific/Honolulu", "Europe/Berlin"]:
            os.environ["TZ"] = zone
            if hasattr(time, "tzset"):
                time.tzset()
            ergebnisse.append(berechne_regel(ID, daten, quellenfassung=FASSUNG))
        assert all(e == ergebnisse[0] for e in ergebnisse)
        assert ergebnisse[0]["wert"] is True
    finally:
        if original is None:
            os.environ.pop("TZ", None)
        else:
            os.environ["TZ"] = original
        if hasattr(time, "tzset"):
            time.tzset()
