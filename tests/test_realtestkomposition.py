"""Obligation activation is separate from actual register/action evidence."""

from euaiact import ermittle_pflicht, pruefe_tatbestand, eingabevertrag

F = "EUAIACT_2026_07_27"


def test_vorfallpflicht_beweist_keine_meldung_oder_minderung():
    duty = ermittle_pflicht(
        "P_AIA_060_007",
        {
            "test_unter_artikel_60": True,
            "schwerwiegender_vorfall_waehrend_realtest_festgestellt": True,
        },
        quellenfassung=F,
    )
    assert duty["wert"]["erfuellung"] == "NICHT_GEPRUEFT"
    assert duty["wert"]["erfuellungskriterien"] == ["AIA_060_007_FOLGEN"]
    evidence = pruefe_tatbestand(
        duty["wert"]["erfuellungskriterien"][0],
        {"realtest_vorfall_nach_artikel_73_gemeldet": False},
        quellenfassung=F,
    )
    assert evidence["wert"] is False


def test_kmu_prioritaetsrecht_ist_keine_tatsaechliche_zulassung():
    duty = ermittle_pflicht(
        "P_AIA_062_001_A",
        dict(
            kmu_status=True,
            reallabor_auswahlkriterien_erfuellt=True,
            reallabor_zulassungsbedingungen_erfuellt=True,
            sitz_oder_zweigniederlassung_in_union=True,
        ),
        quellenfassung=F,
    )
    assert duty["wert"]["erfuellung"] == "NICHT_GEPRUEFT"
    evidence = pruefe_tatbestand(
        duty["wert"]["erfuellungskriterien"][0],
        dict(
            reallabor_kmu_prioritaet_tatsaechlich_gewaehrt=True,
            reallabor_andere_geeignete_kmu_nicht_ausgeschlossen=False,
        ),
        quellenfassung=F,
    )
    assert evidence["wert"] is False


def test_sektorrahmen_uebernimmt_keine_60_4_a_b_c_k_felder():
    fields = eingabevertrag("AIA_060A_005_TESTFOLGEN")["felder"]
    assert "realtest_vor_inverkehrbringen_oder_inbetriebnahme" in fields
    assert "realtest_beendigung_behoerde_mitgeteilt" in fields
    assert not set(fields) & {
        "realtestplan_erstellt",
        "realtest_und_plan_ausdruecklich_genehmigt",
        "realtest_registrierungsweg",
        "systemvorhersagen_empfehlungen_entscheidungen_wirksam_umkehrbar",
    }
    duty = ermittle_pflicht(
        "P_AIA_060A_002",
        dict(mitgliedstaat_entscheidet_anhang_i_b_realtests_zuzulassen=True),
        quellenfassung=F,
    )
    assert "AIA_060A_005_NORMINHALT" in duty["wert"]["erfuellungskriterien"]
    assert duty["wert"]["erfuellung"] == "NICHT_GEPRUEFT"
