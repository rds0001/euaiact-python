"""Historische Aufbewahrung, Anfrage und begrenzte Normvermutung getrennt halten."""

import pytest
from euaiact import ermittle_pflicht, pruefe_tatbestand

FASSUNG = "EUAIACT_2026_07_27"


def test_aufbewahrung_bleibt_nach_ende_der_aktiven_rolle():
    aktuell = ermittle_pflicht(
        "P_AIA_033_001",
        {
            "benannte_stelle": False,
            "spezifische_konformitaetsaufgabe_an_unterauftragnehmer": False,
            "konformitaetsaufgabe_durch_tochterunternehmen": False,
        },
        quellenfassung=FASSUNG,
    )
    historisch = ermittle_pflicht(
        "P_AIA_033_004",
        {
            "aufgabe_als_benannte_stelle_an_unterauftragnehmer_oder_tochterunternehmen_uebertragen": True,
        },
        quellenfassung=FASSUNG,
    )
    assert aktuell["wert"]["ausloeser_erfuellt"] is False
    assert historisch["wert"]["ausloeser_erfuellt"] is True
    assert historisch["wert"]["fristregel_ids"] == ["AIA_033_004_AUFBEWAHRUNGSDAUER"]
    assert historisch["wert"]["erfuellung"] == "NICHT_GEPRUEFT"


def test_aktenaufbewahrung_ist_keine_anfragebezogene_offenlegung():
    basis = {
        "notifizierende_behoerde": True,
        "benennung_ausgesetzt": True,
        "benennung_eingeschraenkt": False,
        "benennung_ganz_oder_teilweise_widerrufen": False,
    }
    aufbewahrung = ermittle_pflicht("P_AIA_036_006", basis, quellenfassung=FASSUNG)
    zugang = ermittle_pflicht(
        "P_AIA_036_006_ZUGANG",
        basis
        | {"betroffene_stellenakten_von_berechtigter_behoerde_angefordert": False},
        quellenfassung=FASSUNG,
    )
    assert aufbewahrung["wert"]["ausloeser_erfuellt"] is True
    assert zugang["wert"]["ausloeser_erfuellt"] is False


@pytest.mark.parametrize("abgedeckt", [True, False])
def test_normvermutung_nur_fuer_abgedeckte_anforderung(abgedeckt):
    ergebnis = pruefe_tatbestand(
        "AIA_032",
        {
            "konformitaetsbewertungsstelle": True,
            "harmonisierte_normreferenz_im_amtsblatt_veroeffentlicht": True,
            "erfuellung_einschlaegiger_normkriterien_nachgewiesen": True,
            "norm_deckt_konkret_gepruefte_artikel_31_anforderung_ab": abgedeckt,
        },
        quellenfassung=FASSUNG,
    )
    assert ergebnis["wert"] is abgedeckt
    assert ergebnis["anwendbarkeit"] == "UNBEKANNT"


def test_auslagerungsausloeser_erteilt_keine_anbieterzustimmung():
    pflicht = ermittle_pflicht(
        "P_AIA_033_001",
        {
            "benannte_stelle": True,
            "spezifische_konformitaetsaufgabe_an_unterauftragnehmer": True,
            "konformitaetsaufgabe_durch_tochterunternehmen": False,
        },
        quellenfassung=FASSUNG,
    )
    zustimmung = pruefe_tatbestand(
        "AIA_033_003_ZUSTIMMUNG",
        {"anbieter_stimmt_konkreter_aufgabenauslagerung_zu": False},
        quellenfassung=FASSUNG,
    )
    assert pflicht["wert"]["ausloeser_erfuellt"] is True
    assert pflicht["wert"]["erfuellung"] == "NICHT_GEPRUEFT"
    assert "AIA_033_003_ZUSTIMMUNG" in pflicht["wert"]["erfuellungskriterien"]
    assert zustimmung["wert"] is False
