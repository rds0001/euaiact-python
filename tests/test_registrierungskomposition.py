"""Cross-rule duty, content and time boundaries for actual registration."""
import json
from pathlib import Path
from euaiact import ermittle_pflicht, pruefe_tatbestand, berechne_regel
F = "EUAIACT_2026_07_27"
CASES = {x["fall_id"]: x for x in json.loads((Path(__file__).parent / "fixtures/grundregeln_referenzen.json").read_text())["faelle"]}

def test_registered_content_does_not_prove_timely_registration():
    case = CASES["REF_REGISTERWEG_035"]
    content = pruefe_tatbestand(case["regel_id"], case["eingaben"], quellenfassung=F)
    duty = ermittle_pflicht("P_AIA_049_002", {"anbieterrolle": True, "anbieter_hat_nichthochrisiko_nach_artikel_6_3_festgestellt": True}, quellenfassung=F)
    time = berechne_regel("AIA_049_ANBIETER_VOR_ERSTEREIGNIS", {"registrierungsabschluss_zeitpunkt": "2028-01-01T10:00:00Z", "erstes_inverkehrbringen_oder_inbetriebnahme_zeitpunkt": "2028-01-01T10:00:00Z"}, quellenfassung=F)
    assert content["wert"] is True
    assert duty["wert"]["ausloeser_erfuellt"] is True
    assert duty["wert"]["erfuellung"] == "NICHT_GEPRUEFT"
    assert duty["wert"]["erfuellungskriterien"] == [case["regel_id"]]
    assert duty["wert"]["fristregel_ids"] == [time["regel_id"]]
    assert time["wert"] is False

def test_empty_restricted_list_cannot_support_complete_registration():
    case = CASES["REF_REGISTERWEG_021"]
    data = case["eingaben"] | {"registrierte_angaben_a": []}
    upper_bound = pruefe_tatbestand("AIA_049_004_DATEN_A", {"registrierte_angaben_a": []}, quellenfassung=F)
    complete = pruefe_tatbestand(case["regel_id"], data, quellenfassung=F)
    assert upper_bound["wert"] is True
    assert complete["wert"] is False

def test_designation_application_and_inclusive_date_are_separate():
    duty = ermittle_pflicht("P_AIA_043_003_ANTRAG", {"stelle_nach_sektorrecht_anhang_i_a_notifiziert": True}, quellenfassung=F)
    date = berechne_regel("AIA_043_003_ANTRAGSTERMIN", {"benennungsantrag_datum": "2028-01-28"}, quellenfassung=F)
    assert duty["wert"]["ausloeser_erfuellt"] is True
    assert duty["wert"]["erfuellung"] == "NICHT_GEPRUEFT"
    assert duty["wert"]["erfuellungskriterien"] == ["AIA_043_003_ANTRAGSKRITERIUM"]
    assert duty["wert"]["fristregel_ids"] == [date["regel_id"]]
    assert date["wert"] is True
