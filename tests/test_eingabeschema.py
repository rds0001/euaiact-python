import pytest
from jsonschema import Draft202012Validator
from euaiact import schema_info, regel_katalog


def test_alle_schemata_gueltig_und_offene_fakten():
    for regel in regel_katalog():
        schema = schema_info(regel["regel_id"] + ":EINGABEN")
        Draft202012Validator.check_schema(schema)
        pruefer = Draft202012Validator(schema)
        assert pruefer.is_valid({})
        assert pruefer.is_valid(dict.fromkeys(schema["properties"]))
        assert not pruefer.is_valid({"unbekanntes_feld": True})


def test_dezimalvertrag_und_enum():
    schema = schema_info("AIA_099_OBERGRENZE:EINGABEN")
    pruefer = Draft202012Validator(schema)
    feld = "weltweiter_vorjahresumsatz_eur"
    for wert in ("0", "100.25", None):
        assert pruefer.is_valid({feld: wert})
    for wert in (0, True, "01", "1e3", "1\n", "1" * 4097):
        assert not pruefer.is_valid({feld: wert})
    assert not pruefer.is_valid({"akteurklasse": "FREI_ERFUNDEN"})
    assert schema["properties"][feld]["anyOf"][1]["x-euaiact-minimum"] == "0"
    assert pruefer.is_valid({feld: "-1"})  # Exakte Grenze prueft der native Kern.


def test_boolean_und_kopie():
    schema = schema_info("AIA_073_MELDEFRISTTAGE:EINGABEN")
    pruefer = Draft202012Validator(schema)
    assert pruefer.is_valid({"todesfall": False})
    assert not pruefer.is_valid({"todesfall": "false"})
    schema["properties"].clear()
    assert schema_info("AIA_073_MELDEFRISTTAGE:EINGABEN")["properties"]
    with pytest.raises(KeyError):
        schema_info("KEINE_REGEL:EINGABEN")


def test_fachvertrag_im_schema_und_transitiv():
    from euaiact import eingabevertrag

    feld = "anzahl_getrennt_bestaetigender_qualifizierter_personen"
    vertrag = eingabevertrag("AIA_014_005_KRITERIUM")["felder"][feld]
    assert "verschiedener natürlicher Personen" in vertrag["definition"]
    eigenschaft = schema_info("AIA_014_005_KRITERIUM:EINGABEN")["properties"][feld]
    assert eigenschaft["description"] == vertrag["definition"]
    assert eigenschaft["x-euaiact-bezugszeit"] == vertrag["bezugszeit"]
    # Herkunft bleibt auch bei transitivem Regelverweis im Schema verfügbar.
    assert schema_info("AIA_003_043:EINGABEN")["properties"]["ki_system"][
        "x-euaiact-herkunft"
    ]
