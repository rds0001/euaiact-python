"""Lokale Grenzen, exakter Roundtrip und nachvollziehbare Feldzuordnung."""

from copy import deepcopy
import pytest
from euaiact import lese_json, schreibe_json, ordne_daten_zu


def test_roundtrip_und_kein_ueberschreiben(tmp_path):
    daten = {
        "leer": {},
        "liste": [],
        "null": None,
        "zahl": 9007199254740991,
        "betrag": "123456789.0000001",
        "text": "Größe München",
        "falsch": False,
    }
    pfad = tmp_path / "daten.json"
    schreibe_json(daten, pfad)
    assert lese_json(pfad) == daten
    with pytest.raises(FileExistsError):
        schreibe_json({}, pfad)
    assert lese_json(pfad) == daten


@pytest.mark.parametrize(
    "inhalt",
    [
        b'{"a":1,"a":2}',
        b'{"a":NaN}',
        b'{"a":1.1}',
        b'{"a":9007199254740992}',
        b'{"a":"\xff"}',
        b'{"":true}',
    ],
)
def test_ungueltige_datei(tmp_path, inhalt):
    pfad = tmp_path / "daten.json"
    pfad.write_bytes(inhalt)
    with pytest.raises(ValueError):
        lese_json(pfad)


@pytest.mark.parametrize(
    "pfad", ["https://example.test/a", "file:///tmp/a", "//server/a", "\\\\server\\a"]
)
def test_externe_pfade_abgelehnt(pfad):
    with pytest.raises(ValueError):
        lese_json(pfad)
    with pytest.raises(ValueError):
        schreibe_json({}, pfad)


def test_mapping_null_herkunft_und_unveraenderlichkeit():
    daten = {"heilzweck": False, "fremd": 7}
    zuordnung = {
        "mappingversion": "firma-1",
        "felder": {"medizinisch": "heilzweck", "arbeitsplatz": "betrieb"},
    }
    vorher = deepcopy((daten, zuordnung))
    ergebnis = ordne_daten_zu(daten, zuordnung)
    assert ergebnis["eingaben"] == {"arbeitsplatz": None, "medizinisch": False}
    assert ergebnis["herkunft"] == [
        {"zielfeld": "arbeitsplatz", "quellfeld": "betrieb", "vorhanden": False},
        {"zielfeld": "medizinisch", "quellfeld": "heilzweck", "vorhanden": True},
    ]
    assert (daten, zuordnung) == vorher


def test_ungueltiger_export_erzeugt_keine_datei(tmp_path):
    pfad = tmp_path / "daten.json"
    with pytest.raises(ValueError):
        schreibe_json({"a": float("nan")}, pfad)
    assert not pfad.exists()


def test_verschachtelung_und_keine_parserrundung(tmp_path):
    pfad = tmp_path / "daten.json"
    for zahl in ("1.0", "1e1", "9007199254740991.1"):
        pfad.write_text('{"a":' + zahl + "}")
        with pytest.raises(ValueError):
            lese_json(pfad)
    pfad.write_text("[" * 102 + "null" + "]" * 102)
    with pytest.raises(ValueError):
        lese_json(pfad)
