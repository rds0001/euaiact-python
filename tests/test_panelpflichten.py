"""Panel duty, majority and calendar compositions from independent examples."""

from euaiact import berechne_regel, berechne_frist, pruefe_tatbestand, ermittle_pflicht

F = "EUAIACT_2026_07_27"


def test_zwei_empfehlungen_benoetigen_eigene_mehrheiten():
    minimum = berechne_regel(
        "PANEL_EINFACHE_MEHRHEIT", {"mitgliederzahl": 60}, quellenfassung=F
    )
    assert minimum["wert"] == 31
    recommendation = pruefe_tatbestand(
        "DVO_0454_005_001_EMPFEHLUNG",
        {
            "panel_hat_vorsitz_aus_mitgliedern_empfohlen": True,
            "panel_hat_stellvertretung_aus_mitgliedern_empfohlen": True,
            "vorsitzempfehlung_hat_einfache_mehrheit_aller_mitglieder": 31
            >= minimum["wert"],
            "stellvertretungsempfehlung_hat_einfache_mehrheit_aller_mitglieder": 30
            >= minimum["wert"],
        },
        quellenfassung=F,
    )
    duty = ermittle_pflicht(
        "P_DVO_0454_005_001",
        {
            "betrachteter_akteur_ist_europaeische_kommission": True,
            "beginn_einer_panelamtszeit": True,
        },
        quellenfassung=F,
    )
    assert recommendation["wert"] is False
    assert duty["wert"]["ausloeser_erfuellt"] is True
    assert duty["wert"]["erfuellung"] == "NICHT_GEPRUEFT"
    assert duty["wert"]["erfuellungskriterien"] == [
        "DVO_0454_005_001_BESTELLUNG",
        "DVO_0454_005_001_EMPFEHLUNG",
        "DVO_0454_005_002_AMTSGLEICHLAUF",
    ]


def test_thematische_anhoerung_publizieren_unabhaengig_von_f017():
    result = ermittle_pflicht(
        "P_DVO_0454_007_005",
        {"thematische_panelanhoerung_tatsaechlich_durchgefuehrt": True},
        quellenfassung=F,
    )
    assert result["wert"]["ausloeser_erfuellt"] is True
    assert result["wert"]["erfuellungskriterien"] == [
        "DVO_0454_007_005_VEROEFFENTLICHUNG"
    ]
    assert result["wert"]["erfuellung"] == "NICHT_GEPRUEFT"


def test_bearbeitung_ab_vollstaendigem_antrag_mit_eigenem_kalender():
    period = berechne_regel("DVO_0454_016_005_BEARBEITUNG", {}, quellenfassung=F)
    # Oct 23 is the qualified complete receipt, not an earlier partial request.
    end = berechne_frist(
        "2026-10-23",
        period["wert"]["anzahl"],
        period["wert"]["einheit"],
        modus="FRIST",
        kalender={
            "von": "2026-10-01",
            "bis": "2026-12-31",
            "feiertage": ["2026-11-06"],
            "bezug": "SYNTHETISCH",
        },
        quellenfassung=F,
    )
    assert end["wert"] == "2026-11-09"
    duty = ermittle_pflicht(
        "P_DVO_0454_016_003_ABLEHNUNGSMITTEILUNG",
        {
            "panelhilfeantrag_durch_ki_buero_nach_16_1_geprueft": True,
            "ki_buero_haelt_panelinformationshilfe_fuer_notwendig": False,
            "ki_buero_haelt_panelinformationshilfe_fuer_verhaeltnismaessig": True,
        },
        quellenfassung=F,
    )
    assert duty["wert"]["fristregel_ids"] == [period["regel_id"]]
    assert duty["wert"]["erfuellung"] == "NICHT_GEPRUEFT"
