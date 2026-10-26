"""An opinion's protection exception does not remove basic transparency duties."""

from euaiact import ermittle_pflicht, pruefe_tatbestand


def test_geschuetzte_stellungnahme_laesst_basisinhalte_unberuehrt():
    fassung = "EUAIACT_2026_07_27"
    basis = ermittle_pflicht(
        "P_DVO_0454_012_BASIS",
        {
            "akteur_ist_sekretariat_des_wissenschaftlichen_gremiums": True,
        },
        quellenfassung=fassung,
    )
    stellungnahme = ermittle_pflicht(
        "P_DVO_0454_012_STELLUNGNAHME",
        {
            "akteur_ist_sekretariat_des_wissenschaftlichen_gremiums": True,
            "panel_stellungnahme_oder_empfehlung_in_erfuellung_artikel_68_3": True,
            "panel_veroeffentlichung_offenbart_geschaeftsgeheimnisse": True,
        },
        quellenfassung=fassung,
    )
    ort = pruefe_tatbestand(
        "DVO_0454_012_PUBLIKATIONSWEG",
        {
            "panel_informationen_auf_eigens_vorgesehener_kommissionswebsite": False,
            "panel_informationen_ohne_unangemessene_verzoegerung_bereitgestellt": True,
        },
        quellenfassung=fassung,
    )
    assert basis["wert"]["ausloeser_erfuellt"] is True
    assert stellungnahme["wert"]["ausloeser_erfuellt"] is False
    assert stellungnahme["entscheidungsrelevante_luecken"] == []
    assert basis["wert"]["erfuellung"] == "NICHT_GEPRUEFT"
    assert basis["wert"]["erfuellungskriterien"] == [
        "DVO_0454_012_BASISINHALTE",
        "DVO_0454_012_PUBLIKATIONSWEG",
    ]
    assert ort["wert"] is False
