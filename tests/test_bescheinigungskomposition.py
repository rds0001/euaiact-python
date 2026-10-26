"""A positive assessment is distinct from actual certificate issuance."""

from euaiact import ermittle_pflicht, pruefe_tatbestand


def test_positive_bewertung_ersetzt_keine_bescheinigung():
    f = "EUAIACT_2026_07_27"
    p = ermittle_pflicht(
        "P_AIA_ANH_VII_4_6_ERTEILUNG",
        {
            "verfahren_nach_anhang_vii_einschlaegig": True,
            "ergebnis_abschnitt_2_stellenbewertung": "KONFORM",
        },
        quellenfassung=f,
    )
    ausstellung = pruefe_tatbestand(
        "AIA_ANH_VII_4_6_AUSSTELLUNG",
        {
            "stelle_hat_unions_technikbescheinigung_fuer_bewertetes_system_ausgestellt": False,
        },
        quellenfassung=f,
    )
    assert p["wert"]["ausloeser_erfuellt"] is True
    assert p["wert"]["erfuellung"] == "NICHT_GEPRUEFT"
    assert p["wert"]["erfuellungskriterien"] == [
        "AIA_ANH_VII_4_6_MITTEILUNG",
        "AIA_ANH_VII_4_6_AUSSTELLUNG",
        "AIA_ANH_VII_4_6_BESCHEINIGUNGSINHALTE",
    ]
    assert ausstellung["wert"] is False
