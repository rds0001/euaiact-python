"""Source-closure workflows keep due dates, competence and actual acts separate."""

from euaiact import berechne_regel, pruefe_tatbestand, ermittle_pflicht, eingabevertrag

F = "EUAIACT_2026_07_27"


def t(id, data):
    return pruefe_tatbestand(id, data, quellenfassung=F)


def positive(id):
    return dict.fromkeys(eingabevertrag(id)["felder"], True)


def test_evaluationszyklen_ersetzen_keinen_tatsaechlichen_bericht():
    four = berechne_regel(
        "AIA_112_002_TERMIN", dict(evaluationszyklus_index=1), quellenfassung=F
    )
    three = berechne_regel(
        "AIA_112_007_TERMIN", dict(evaluationszyklus_index=1), quellenfassung=F
    )
    assert four["wert"] == "2032-08-02" and three["wert"] == "2031-08-02"
    duty = ermittle_pflicht(
        "P_AIA_112_002", dict(schluss_kommission=True), quellenfassung=F
    )
    assert duty["wert"]["fristregel_ids"] == ["AIA_112_002_TERMIN"]
    assert duty["wert"]["erfuellung"] == "NICHT_GEPRUEFT"
    data = positive("AIA_112_002_KRITERIEN")
    data[
        "evaluation_112_bericht_oder_feststellungen_dem_parlament_und_rat_uebermittelt"
    ] = False
    assert t("AIA_112_002_KRITERIEN", data)["wert"] is False


def test_kompetenzmassnahmen_sind_keine_individuelle_erfolgsgarantie():
    duty = ermittle_pflicht(
        "P_AIA_004_001",
        dict(ki_system=True, anbieterrolle=False, betreiberrolle=True),
        quellenfassung=F,
    )
    assert (
        duty["wert"]["ausloeser_erfuellt"] is True
        and duty["wert"]["erfuellung"] == "NICHT_GEPRUEFT"
    )
    data = dict(
        ki_kompetenz_massnahmen_fuer_personal_und_im_auftrag_handlende_personen=True,
        ki_kompetenz_technisches_wissen_erfahrung_bildung_ausbildung_beruecksichtigt=True,
        ki_kompetenz_konkreter_einsatzkontext_beruecksichtigt=True,
        ki_kompetenz_betroffene_personen_oder_gruppen_beruecksichtigt=True,
    )
    assert t("AIA_004_001_KRITERIEN", data)["wert"] is True
    data["ki_kompetenz_konkreter_einsatzkontext_beruecksichtigt"] = None
    assert t("AIA_004_001_KRITERIEN", data)["status"] == "EINGABE_FEHLT"


def test_normreferenz_ist_keine_tatsaechliche_spezifikationsaufhebung():
    data = dict(
        harmonisierte_normreferenz_fuer_ersetzende_anforderungen_im_amtsblatt_veroeffentlicht=True,
        gemeinsame_spezifikation_deckt_dieselben_anforderungen_oder_pflichten_wie_norm=True,
    )
    duty = ermittle_pflicht("P_AIA_041_004_AUFHEBUNG", data, quellenfassung=F)
    assert duty["wert"]["ausloeser_erfuellt"] is True
    assert (
        t(
            "AIA_041_004_AUFHEBUNGSNACHWEIS",
            dict(
                kommission_hat_durch_norm_abgedeckte_spezifikationsakte_oder_teile_aufgehoben=False
            ),
        )["wert"]
        is False
    )


def test_vertraulichkeit_verlangt_mehr_als_einen_vertrag():
    duty = ermittle_pflicht(
        "P_AIA_078_002_SICHERHEIT",
        dict(
            an_ai_act_anwendung_beteiligte_behoerde=True,
            information_bei_ai_act_aufgaben_erlangt=True,
        ),
        quellenfassung=F,
    )
    assert duty["wert"]["ausloeser_erfuellt"] is True
    assert (
        t(
            "AIA_078_002_SICHERHEITSNACHWEIS",
            dict(
                behoerde_hat_angemessene_wirksame_cybersicherheit_fuer_erlangte_information_eingerichtet=False
            ),
        )["wert"]
        is False
    )
    request = ermittle_pflicht(
        "P_AIA_078_002_ANFORDERUNG",
        dict(
            an_ai_act_anwendung_beteiligte_behoerde=True,
            behoerde_fordert_daten_fuer_ai_act_befugnisse_an=True,
        ),
        quellenfassung=F,
    )
    assert request["wert"]["ausloeser_erfuellt"] is True
    assert (
        t(
            "AIA_078_002_ERFORDERLICHKEIT",
            dict(
                behoerdlich_angeforderte_daten_strikt_fuer_risiko_und_befugnisse_erforderlich=False
            ),
        )["wert"]
        is False
    )


def test_gross_it_bestandsfrist_ersetzt_nicht_evaluationsnachweis():
    from euaiact import pruefe_bestandsfrist

    end = pruefe_bestandsfrist(
        "GROSS_IT_ANHANG_X",
        "2031-01-02",
        ereignisse={"inverkehrbringen": {"erfolgt": True, "datum": "2026-01-01"}},
        quellenfassung=F,
    )
    assert end["wert"]["friststatus"] == "NACH_FRISTTAG"
    duty = ermittle_pflicht(
        "P_AIA_111_001_EVALUATION",
        {
            "evaluation_betrifft_gross_it_system_nach_anhang_x": True,
            "evaluation_nach_einrichtungsrechtsakt_oder_bei_dessen_ersetzung_aenderung": True,
        },
        quellenfassung=F,
    )
    assert duty["wert"]["ausloeser_erfuellt"] is True
    assert duty["wert"]["erfuellung"] == "NICHT_GEPRUEFT"
    assert (
        t(
            "AIA_111_001_EVALUATIONSNACHWEIS",
            {"ai_act_anforderungen_in_gross_it_evaluation_beruecksichtigt": False},
        )["wert"]
        is False
    )
