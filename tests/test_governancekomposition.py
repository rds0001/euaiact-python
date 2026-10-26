"""Quorum und Ereignisse explizit mit institutionellen Kriterien verknüpfen."""

import pytest
from euaiact import berechne_frist, berechne_regel, ermittle_pflicht, pruefe_tatbestand

FASSUNG = "EUAIACT_2026_07_27"


@pytest.mark.parametrize(
    "stimmen,inhalt,erwartet", [(17, True, False), (18, True, True), (18, False, False)]
)
def test_quorum_ersetzt_keine_geschaeftsordnungsinhalte(stimmen, inhalt, erwartet):
    quorum = berechne_regel(
        "AIA_065_005_ZWEIDRITTELMEHRHEIT",
        {"benannte_mitgliedstaatenvertreter": 27},
        quellenfassung=FASSUNG,
    )
    assert quorum["wert"] == 18
    kriterium = pruefe_tatbestand(
        "AIA_065_005_KRITERIEN",
        {
            "ki_gremium_geschaeftsordnung_von_benannten_vertretern_mit_zweidritteln_angenommen": stimmen
            >= quorum["wert"],
            "ki_gremium_geschaeftsordnung_regelt_vorsitzauswahl_amtsdauer_und_aufgaben": inhalt,
            "ki_gremium_geschaeftsordnung_regelt_abstimmung_und_organisation_einschliesslich_untergruppen": True,
        },
        quellenfassung=FASSUNG,
    )
    assert kriterium["wert"] is erwartet
    pflicht = ermittle_pflicht(
        "P_AIA_065_005",
        {"betrachteter_akteur_ist_europaeisches_ki_gremium": True},
        quellenfassung=FASSUNG,
    )
    assert pflicht["wert"]["ausloeser_erfuellt"] is True
    assert pflicht["wert"]["erfuellung"] == "NICHT_GEPRUEFT"
    assert pflicht["wert"]["fristregel_ids"] == []


@pytest.mark.parametrize(
    "empfang,erwartet", [(False, False), (True, True), (None, None)]
)
def test_weiterleitung_setzt_empfang_voraus(empfang, erwartet):
    pflicht = ermittle_pflicht(
        "P_AIA_070_006_WEITERLEITUNG",
        {
            "betrachteter_akteur_ist_europaeische_kommission": True,
            "kommission_hat_ressourceninformation_nach_artikel_70_6_erhalten": empfang,
        },
        quellenfassung=FASSUNG,
    )
    assert pflicht["wert"]["ausloeser_erfuellt"] is erwartet
    assert pflicht["wert"]["erfuellung"] == "NICHT_GEPRUEFT"
    assert pflicht["anwendbarkeit"] == "UNBEKANNT"


@pytest.mark.parametrize(
    "regel,anker,erwartet",
    [
        ("AIA_065_003_AMTSDAUER", "2026-08-03", "2029-08-03"),
        ("AIA_067_004_AMTSDAUER", "2026-08-03", "2028-08-03"),
        ("AIA_067_004_VERLAENGERUNGSHOECHSTDAUER", "2028-08-03", "2032-08-03"),
        ("AIA_067_006_AMTSDAUER", "2026-08-03", "2028-08-03"),
        ("AIA_070_006_BERICHTSINTERVALL", "2025-08-02", "2027-08-02"),
        ("AIA_070_006_BERICHTSINTERVALL", "2027-08-02", "2029-08-02"),
    ],
)
def test_explizite_kalenderankerkette(regel, anker, erwartet):
    # FESTER_TERMIN ist hier bewusst der gewählte Kalendervergleich, kein
    # automatisch abgeleitetes Fristregime und keine neue Bestellungsentscheidung.
    dauer = berechne_regel(regel, {}, quellenfassung=FASSUNG)
    ende = berechne_frist(
        anker,
        dauer["wert"]["anzahl"],
        dauer["wert"]["einheit"],
        modus="FESTER_TERMIN",
        quellenfassung=FASSUNG,
    )
    assert ende["wert"] == erwartet
    assert ende["anwendbarkeit"] == "UNBEKANNT"


@pytest.mark.parametrize(
    "regel", ["AIA_065_003_VERLAENGERUNG", "AIA_067_006_VERLAENGERUNG"]
)
def test_dauerparameter_erteilt_keine_zweite_verlaengerung(regel):
    feld = "bisherige_verlaengerungen_der_amtszeit"
    erlaubt = pruefe_tatbestand(regel, {feld: 0}, quellenfassung=FASSUNG)
    abgelehnt = pruefe_tatbestand(regel, {feld: 1}, quellenfassung=FASSUNG)
    assert erlaubt["wert"] is True
    assert abgelehnt["wert"] is False
