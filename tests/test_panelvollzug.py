"""Independent panel sequences: distinct majority, actual act and chronology."""

from euaiact import berechne_regel, pruefe_tatbestand, ermittle_pflicht

F = "EUAIACT_2026_07_27"


def t(id, data):
    return pruefe_tatbestand("DVO_0454_" + id, data, quellenfassung=F)


def p(id, data):
    return ermittle_pflicht("P_DVO_0454_" + id, data, quellenfassung=F)


def test_drittel_autorisiert_antrag_aber_keine_warnung():
    third = berechne_regel(
        "PANEL_DRITTEL_AUTORISIERUNG", {"mitgliederzahl": 60}, quellenfassung=F
    )["wert"]
    majority = berechne_regel(
        "PANEL_EINFACHE_MEHRHEIT", {"mitgliederzahl": 60}, quellenfassung=F
    )["wert"]
    assert (third, majority) == (20, 31)
    request = t(
        "015_002_ANTRAGSBEFUGNIS",
        {
            "antragsteller_ist_mitglied_des_wissenschaftlichen_gremiums": True,
            "antragsteller_vom_sekretariat_zum_berichterstatter_der_aufgabe_bestellt": True,
            "mindestens_ein_drittel_aller_panelmitglieder_hat_antragsteller_autorisiert": 20
            >= third,
        },
    )
    warning = t(
        "018_001_MEHRHEITSBESCHLUSS",
        {
            "panelwarnung_von_mindestens_einfacher_mehrheit_aller_mitglieder_beschlossen": 20
            >= majority
        },
    )
    assert request["wert"] is True and warning["wert"] is False


def test_entlassung_ersetzt_keine_tatsaechliche_neubestellung():
    duty = p(
        "004_003_ERSATZBESTELLUNG",
        {
            "panel_experte_tatsaechlich_entlassen": True,
            "entlassung_waehrend_laufender_amtszeit": True,
        },
    )
    actual = t(
        "004_003_ERSATZNACHWEIS",
        {"ersatzexperte_tatsaechlich_durch_kommission_bestellt": False},
    )
    assert duty["wert"]["ausloeser_erfuellt"] is True
    assert "DVO_0454_004_003_ERSATZNACHWEIS" in duty["wert"]["erfuellungskriterien"]
    assert duty["wert"]["erfuellung"] == "NICHT_GEPRUEFT" and actual["wert"] is False


def test_keine_massnahme_ist_keine_automatische_schliessung():
    assessed = t(
        "019_001_ENTSCHEIDUNG",
        {
            "ki_buero_hat_panelwarnung_tatsaechlich_bewertet": True,
            "ki_buero_hat_ueber_91_bis_93_massnahmen_tatsaechlich_entschieden": True,
        },
    )
    duty = p(
        "019_001_WARNUNGSSCHLIESSUNG",
        {
            "ki_buero_hat_qualifizierte_warnung_nach_90_1_bewertet": True,
            "ki_buero_hat_entschieden_keine_massnahmen_nach_91_bis_93_einzuleiten": True,
        },
    )
    actual = t(
        "019_001_SCHLIESSUNGSNACHWEIS",
        {"qualifizierte_panelwarnung_tatsaechlich_geschlossen": None},
    )
    assert assessed["wert"] is True and duty["wert"]["ausloeser_erfuellt"] is True
    assert duty["wert"]["erfuellung"] == "NICHT_GEPRUEFT"
    assert actual["status"] == "EINGABE_FEHLT" and actual["wert"] is None


def test_nachgereichte_zugangserklaerung_ersetzt_keine_vorlage_vorab():
    content = t(
        "017_003_VORABUNTERLAGEN",
        {
            "berichterstatter_hat_alleinige_verwendung_fuer_15_3_zwecke_erklaert": True,
            "berichterstatter_hat_modalitaeten_und_sicherungen_vertraulicher_handhabung_beschrieben": True,
        },
    )
    chronology = t(
        "017_003_VORHER",
        {
            "ki_buero_hat_berichterstatter_vor_zugang_zu_vorabunterlagen_aufgefordert": True,
            "panel_vorabunterlagen_tatsaechlich_vor_zugangsgewaehrung_eingereicht": False,
        },
    )
    duty = p(
        "017_ZUGANG",
        {"ki_buero_gewaehrt_panelzugang_zu_angeforderter_information": True},
    )
    assert content["wert"] is True and chronology["wert"] is False
    assert "DVO_0454_017_003_VORHER" in duty["wert"]["erfuellungskriterien"]
    assert duty["wert"]["erfuellung"] == "NICHT_GEPRUEFT"
