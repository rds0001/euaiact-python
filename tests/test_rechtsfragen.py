"""Offene Rechtsauslegung ist kein fehlendes oder überschreibbares Unternehmensdatum."""

from copy import deepcopy
import json
from pathlib import Path
from jsonschema import Draft202012Validator
from euaiact import pruefe_tatbestand, schema_info, eingabevertrag

FAELLE = {
    x["fall_id"]: x
    for x in json.loads(
        (Path(__file__).parent / "fixtures/grundregeln_referenzen.json").read_text()
    )["faelle"]
}
FALL = FAELLE["REF_BEZIEHUNG_SMC_INVESTORENAUSNAHME_ANGEL_GRENZE"]


def pruefen(eingaben):
    return pruefe_tatbestand(
        "SMC_INVESTORENAUSNAHME", eingaben, quellenfassung="EUAIACT_2026_07_27"
    )


def test_offene_rechtsfrage_ohne_erfundene_fehlende_eingabe():
    e = pruefen(FALL["eingaben"])
    assert e["status"] == "REGEL_UNGEKLAERT" and e["wert"] is None
    assert e["entscheidungsrelevante_luecken"] == []
    assert e["entscheidungsschritte"][-1]["offene_rechtsfragen"] == ["F015"]
    assert any("F015" in h for h in e["hinweise"])
    assert "F015" not in eingabevertrag("SMC_INVESTORENAUSNAHME")["felder"]
    Draft202012Validator(schema_info()).validate(e)


def test_datenluecke_und_rechtsfrage_getrennt():
    daten = deepcopy(FALL["eingaben"])
    daten.pop("business_angel_gesamtinvestition_im_selben_unternehmen_eur")
    e = pruefen(daten)
    assert e["status"] == "REGEL_UNGEKLAERT"
    assert e["entscheidungsrelevante_luecken"] == [
        "business_angel_gesamtinvestition_im_selben_unternehmen_eur"
    ]
    assert e["entscheidungsschritte"][-1]["offene_rechtsfragen"] == ["F015"]


def test_entscheidungsunerhebliche_rechtsfrage_blockiert_nicht():
    for daten, wert in [
        (
            dict(
                FALL["eingaben"],
                investor_universitaet_oder_nichtgewinnorientiertes_forschungszentrum=True,
            ),
            True,
        ),
        (
            dict(
                FALL["eingaben"],
                qualifizierte_investoren_einzeln_oder_gemeinsam_mit_unternehmen_verbunden=True,
            ),
            False,
        ),
    ]:
        e = pruefen(daten)
        assert e["status"] == "AUSGEWERTET" and e["wert"] is wert
        assert "offene_rechtsfragen" not in e["entscheidungsschritte"][-1]
        assert not any(h.startswith("Offene Rechtsfrage ") for h in e["hinweise"])


def test_rechtsfrage_nicht_durch_nutzerfeld_ueberschreibbar():
    e = pruefen(dict(FALL["eingaben"], rechtsfrage_f015=False))
    assert e["status"] == "EINGABE_UNGUELTIG"
