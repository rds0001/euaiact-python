"""Historische Verfügbarkeit und konkrete Vorlage sind verschiedene Pflichten."""

from euaiact import ermittle_pflicht, pruefe_tatbestand

FASSUNG = "EUAIACT_2026_07_27"


def test_historische_aufbewahrung_nach_ende_aktueller_rolle():
    aktuell = ermittle_pflicht(
        "P_AIA_047_001",
        {"anbieterrolle": False, "hochrisikosystem": True},
        quellenfassung=FASSUNG,
    )
    historisch = ermittle_pflicht(
        "P_AIA_047_001_AUFBEWAHRUNG",
        {
            "akteur_hat_hochrisikosystem_als_anbieter_inverkehrgebracht_oder_inbetriebgenommen": True
        },
        quellenfassung=FASSUNG,
    )
    assert aktuell["wert"]["ausloeser_erfuellt"] is False
    assert historisch["wert"]["ausloeser_erfuellt"] is True
    assert historisch["wert"]["erfuellung"] == "NICHT_GEPRUEFT"
    assert historisch["wert"]["fristregel_ids"] == ["AIA_047_001_AUFBEWAHRUNGSDAUER"]


def test_vorlage_ist_nicht_durch_verfuegbarkeit_erfuellt():
    verfuegbar = pruefe_tatbestand(
        "AIA_047_001_VERFUEGBARKEIT",
        {
            "eu_erklaerung_zustaendigen_nationalen_behoerden_verfuegbar": True,
            "eu_erklaerung_zehnjahreszeitraum_ab_markt_oder_inbetriebnahme_eingehalten": True,
        },
        quellenfassung=FASSUNG,
    )
    vorlage = pruefe_tatbestand(
        "AIA_047_001_KOPIEKRITERIUM",
        {
            "angeforderte_eu_erklaerungskopie_zustaendiger_nationaler_behoerde_vorgelegt": False
        },
        quellenfassung=FASSUNG,
    )
    pflicht = ermittle_pflicht(
        "P_AIA_047_001_KOPIE",
        {
            "anbieterrolle": True,
            "hochrisikosystem": True,
            "zustaendige_nationale_behoerde_fordert_eu_erklaerung_an": True,
        },
        quellenfassung=FASSUNG,
    )
    assert verfuegbar["wert"] is True
    assert vorlage["wert"] is False
    assert pflicht["wert"]["ausloeser_erfuellt"] is True
    assert pflicht["wert"]["erfuellungskriterien"] == ["AIA_047_001_KOPIEKRITERIUM"]
    assert pflicht["wert"]["erfuellung"] == "NICHT_GEPRUEFT"
