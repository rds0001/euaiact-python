"""Distinct notification, approval and training-specific rejection consequences."""

from euaiact import ermittle_pflicht

F = "EUAIACT_2026_07_27"


def test_ergänzungsweg_ohne_genehmigung_verlangt_mitteilung_aber_keine_ausstellung():
    daten = {
        "verfahren_nach_anhang_vii_einschlaegig": True,
        "stelle_hat_ergaenzungsweg_fuer_konkrete_systemaenderungen_festgelegt": True,
    }
    mitteilung = ermittle_pflicht(
        "P_AIA_ANH_VII_4_7_ERGAENZUNGSBEWERTUNG", daten, quellenfassung=F
    )
    ausstellung = ermittle_pflicht(
        "P_AIA_ANH_VII_4_7_ERGAENZUNG",
        daten
        | {
            "stelle_hat_systemaenderungen_im_ergaenzungsweg_genehmigt": False,
        },
        quellenfassung=F,
    )
    assert mitteilung["wert"]["ausloeser_erfuellt"] is True
    assert ausstellung["wert"]["ausloeser_erfuellt"] is False
    assert mitteilung["wert"]["erfuellung"] == "NICHT_GEPRUEFT"
    assert mitteilung["wert"]["erfuellungskriterien"] == [
        "AIA_ANH_VII_4_7_ERGAENZUNGSMITTEILUNG"
    ]
    assert ausstellung["wert"]["erfuellungskriterien"] == [
        "AIA_ANH_VII_4_7_ERGAENZUNGSAUSSTELLUNG"
    ]


def test_ablehnung_aus_anderem_grund_verlangt_keine_trainingsspezifische_begruendung():
    daten = {
        "verfahren_nach_anhang_vii_einschlaegig": True,
        "ergebnis_abschnitt_2_stellenbewertung": "NICHT_KONFORM",
    }
    allgemein = ermittle_pflicht("P_AIA_ANH_VII_4_6_ABLEHNUNG", daten, quellenfassung=F)
    training = ermittle_pflicht(
        "P_AIA_ANH_VII_4_6_TRAININGBEGRUENDUNG",
        daten
        | {
            "system_erfuellt_anforderung_an_trainingsdaten_nicht": False,
        },
        quellenfassung=F,
    )
    assert allgemein["wert"]["ausloeser_erfuellt"] is True
    assert training["wert"]["ausloeser_erfuellt"] is False
    assert training["wert"]["erfuellungskriterien"] == [
        "AIA_ANH_VII_4_6_TRAININGABLEHNUNGSKRITERIEN"
    ]
