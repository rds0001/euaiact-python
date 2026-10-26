"""Market procedure stages remain separate from completed acts."""

from euaiact import (
    ermittle_pflicht,
    pruefe_tatbestand,
    eingabevertrag,
    pflicht_katalog,
    regel_info,
)

F = "EUAIACT_2026_07_27"


def test_begruendeter_quellcodeanspruch_ist_keine_zugangsgewaehrung():
    inputs = dict(
        marktaufsicht_quellcodezugang_begruendet_beantragt=True,
        marktaufsicht_quellcodezugang_fuer_abschnitt_2_bewertung_notwendig=True,
        marktaufsicht_daten_dokumentbasierte_tests_erschoepft_oder_unzureichend=True,
    )
    duty = ermittle_pflicht("P_AIA_074_013_QUELLCODE", inputs, quellenfassung=F)["wert"]
    assert duty["ausloeser_erfuellt"] is True
    assert duty["erfuellung"] == "NICHT_GEPRUEFT"
    result = pruefe_tatbestand(
        duty["erfuellungskriterien"][0],
        dict(anbieter_hat_qualifiziert_erforderlichen_quellcodezugang_gewaehrt=False),
        quellenfassung=F,
    )
    assert result["wert"] is False
    inputs[
        "marktaufsicht_daten_dokumentbasierte_tests_erschoepft_oder_unzureichend"
    ] = False
    assert (
        ermittle_pflicht("P_AIA_074_013_QUELLCODE", inputs, quellenfassung=F)["wert"][
            "ausloeser_erfuellt"
        ]
        is False
    )


def test_spezialempfaenger_und_musspflichten_nicht_vermischt():
    duty = ermittle_pflicht(
        "P_AIA_075_001A_MELDUNG",
        dict(
            anbieterrolle=True,
            hochrisikosystem=True,
            ki_system=True,
            system_ist_oder_integriert_in_benannte_sehr_grosse_onlineplattform_oder_suchmaschine=True,
            schwerwiegender_vorfall_identifiziert=True,
            verletzung_unionsrechtlicher_grundrechtsschutzpflicht=True,
        ),
        quellenfassung=F,
    )["wert"]
    assert duty["ausloeser_erfuellt"] is True
    assert duty["erfuellungskriterien"] == ["AIA_075_001A_EMPFAENGER"]
    assert (
        pruefe_tatbestand(
            "AIA_075_001A_EMPFAENGER",
            dict(marktkooperation_vorfall_tatsaechlich_an_ki_buero_gemeldet=False),
            quellenfassung=F,
        )["wert"]
        is False
    )
    # Special law imports73(2)-(9), not the medical-recipient rule73(10).
    assert (
        "vorfallmeldung_an_national_gewaehlte_medizinproduktbehoerde"
        not in eingabevertrag("AIA_075_001A_EMPFAENGER")["felder"]
    )
    assert regel_info("AIA_074_007_EZB_KONTEXT")["regelart"] == "SOLL_MELDEKONTEXT"
    assert not any(
        p["ausloeser_regel"] == "AIA_074_007_EZB_KONTEXT" for p in pflicht_katalog()
    )


def test_einwandfreie_massnahme_und_kommissionsbeschluss_sind_verschieden():
    fiction = pruefe_tatbestand(
        "AIA_079_008",
        dict(
            massnahme_nach_artikel_79_5_notifiziert=True,
            einschlaegige_artikel_79_8_einwandfrist_abgelaufen=True,
            mitgliedstaat_marktueberwachung_hat_fristgerecht_einwand_erhoben=False,
            kommission_hat_artikel_79_einwand_fristgerecht_erhoben=False,
        ),
        quellenfassung=F,
    )
    assert fiction["wert"] is True
    # No commission decision is inferred from this legal fiction.
    assert (
        pruefe_tatbestand("AIA_081_002_MASSNAHME", {}, quellenfassung=F)["wert"] is None
    )
    withdrawal = ermittle_pflicht(
        "P_AIA_081_002_RUECKNAHME",
        dict(kommissionsentscheidung_nationale_massnahme="UNGERECHTFERTIGT"),
        quellenfassung=F,
    )["wert"]
    assert withdrawal["ausloeser_erfuellt"] is True
    assert (
        pruefe_tatbestand(
            withdrawal["erfuellungskriterien"][0],
            dict(
                marktverfahren_81_ungerechtfertigte_nationale_massnahme_zurueckgenommen=False,
                marktverfahren_81_kommission_ueber_massnahmenruecknahme_informiert=True,
            ),
            quellenfassung=F,
        )["wert"]
        is False
    )


def test_publikationsinhalt_allein_ist_keine_veroeffentlichung():
    duty = ermittle_pflicht(
        "P_AIA_075D_004",
        dict(ki_buero_hat_beschluss_nach_75b_erlassen=True),
        quellenfassung=F,
    )["wert"]
    assert duty["ausloeser_erfuellt"] is True
    assert {"AIA_075D_004_KRITERIEN", "AIA_075D_004_PUBLIKATIONSNACHWEIS"} <= set(
        duty["erfuellungskriterien"]
    )
    assert (
        pruefe_tatbestand(
            "AIA_075D_004_KRITERIEN",
            dict(
                veroeffentlichung_nennt_parteien=True,
                veroeffentlichung_enthaelt_wesentlichen_beschlussinhalt=True,
                veroeffentlichung_beruecksichtigt_rechte_und_berechtigte_geheimhaltungsinteressen=True,
                sanktion_im_beschluss_verhaengt=False,
            ),
            quellenfassung=F,
        )["wert"]
        is True
    )
    assert (
        pruefe_tatbestand(
            "AIA_075D_004_PUBLIKATIONSNACHWEIS",
            dict(marktvollzug_75b_75c_beschluss_tatsaechlich_veroeffentlicht=False),
            quellenfassung=F,
        )["wert"]
        is False
    )
