"""GPAI procedural consequences are not inferred from permissibility or requests."""

from euaiact import ermittle_pflicht, pruefe_tatbestand, eingabevertrag, pflicht_katalog

F = "EUAIACT_2026_07_27"


def inputs(rule_id, dossier):
    # Explicitly map the local dossier onto each public input contract.
    fields = eingabevertrag(rule_id)["felder"]
    return {k: v for k, v in dossier.items() if k in fields}


def t(id, data):
    rule_id = "DVO_1755_" + id
    return pruefe_tatbestand(rule_id, inputs(rule_id, data), quellenfassung=F)


def p(id, data):
    duty_id = "P_DVO_1755_" + id
    rule_id = next(
        x["ausloeser_regel"] for x in pflicht_katalog() if x["pflicht_id"] == duty_id
    )
    return ermittle_pflicht(duty_id, inputs(rule_id, data), quellenfassung=F)


def test_signierter_zulaessiger_versand_ist_kein_empfang():
    data = dict(
        verfahrensdokument_oder_information_digital_uebermittelt=True,
        verfahrensdokument_tatsaechlich_per_einschreiben_an_kommission_uebermittelt=False,
        verfahrensdokument_tatsaechlich_von_hand_an_kommission_uebermittelt=False,
        uebermittlung_betrifft_dokument=True,
        anzahl_eidas_konformer_qualifizierter_signaturen=1,
        digitale_uebermittlung_an_kommission=True,
        kommission_hat_empfangsbestaetigung_abgesandt=True,
        dokument_oder_teil_nicht_funktionsfaehig_oder_unbrauchbar=True,
        dokument_enthaelt_viren_schadsoftware_oder_andere_bedrohungen=False,
        dokument_enthaelt_elektronische_signatur=True,
        signaturgueltigkeit_durch_kommission_verifizierbar=True,
    )
    assert t("014_UEBERMITTLUNGSWEG", data)["wert"] is True
    assert t("014_003_EMPFANGSVORAUSSETZUNG", data)["wert"] is False
    assert p("014_006_MANGELMITTEILUNG", data)["wert"]["ausloeser_erfuellt"] is True


def test_einstellungsgrund_ersetzt_keinen_beschluss_oder_anhoerung():
    data = dict(
        sanktionsverfahren_nach_dvo_artikel_5_eroeffnet=True,
        kommission_hat_fehlende_gruende_fuer_101_1_entscheidung_festgestellt=True,
        verfahren_auf_beschwerde_nachgelagerter_anbieter_89_2_eroeffnet=True,
    )
    assert p("006_001_EINSTELLUNG", data)["wert"]["ausloeser_erfuellt"] is True
    assert p("006_001_BESCHWERDEANHOERUNG", data)["wert"]["ausloeser_erfuellt"] is True
    assert (
        t(
            "006_001_EINSTELLUNGSNACHWEIS",
            dict(
                gpai_sanktionsverfahren_tatsaechlich_durch_kommissionsbeschluss_eingestellt=False
            ),
        )["wert"]
        is False
    )
    assert (
        t(
            "006_001_ANHOERUNGSNACHWEIS",
            dict(
                nachgelagerter_beschwerdefuehrer_hat_vor_einstellungsbeschluss_aeusserungsmoeglichkeit_erhalten=None
            ),
        )["status"]
        == "EINGABE_FEHLT"
    )


def test_begruendeter_antrag_verlaengert_frist_nicht():
    request = t(
        "013_002_VERLAENGERUNGSANTRAG",
        dict(
            frist_von_kommission_gesetzt=True,
            verlaengerung_vom_betroffenen_anbieter_beantragt=True,
            verlaengerungsantrag_vor_fristablauf=True,
            verlaengerungsantrag_begruendet=True,
            fristverlaengerung_angemessen=True,
        ),
    )
    granted = t(
        "013_002_BEWILLIGUNG",
        dict(kommission_hat_konkrete_fristverlaengerung_tatsaechlich_gewaehrt=False),
    )
    assert request["wert"] is True and granted["wert"] is False


def test_beratermeldung_ersetzt_nicht_meldung_des_adressaten():
    duty = p(
        "008_003_BEZIEHUNGSMELDUNG",
        dict(
            benannter_externer_berater_oder_experte_mit_aktenzugang=True,
            nachtraeglich_beschaeftigungsbeziehung_oder_vergleichbares_eingegangen=True,
            neue_beziehung_zum_adressaten=True,
            neue_beziehung_zu_unternehmen_auf_selben_maerkten=False,
            beziehung_waehrend_untersuchung_eingegangen=False,
            beziehung_innerhalb_drei_jahren_nach_untersuchungsende_eingegangen=True,
        ),
    )
    actual = t(
        "008_003_MELDUNGSNACHWEIS",
        dict(
            berater_hat_neue_beziehungsbedingungen_unverzueglich_kommission_mitgeteilt=True,
            adressat_hat_neue_beraterbeziehungsbedingungen_unverzueglich_kommission_mitgeteilt=False,
        ),
    )
    assert duty["wert"]["ausloeser_erfuellt"] is True
    assert "DVO_1755_008_003_MELDUNGSNACHWEIS" in duty["wert"]["erfuellungskriterien"]
    assert duty["wert"]["erfuellung"] == "NICHT_GEPRUEFT" and actual["wert"] is False
