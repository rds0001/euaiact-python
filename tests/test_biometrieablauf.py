"""Bounded biometric workflows with explicit local time qualification."""

import json
from pathlib import Path
import pytest
from euaiact import berechne_regel, pruefe_tatbestand, eingabevertrag

F = "EUAIACT_2026_07_27"
REFS = json.loads(
    (Path(__file__).parent / "fixtures/grundregeln_referenzen.json").read_text()
)["faelle"]


def t(id, d):
    fields = eingabevertrag(id)["felder"]
    return pruefe_tatbestand(
        id, {k: v for k, v in d.items() if k in fields}, quellenfassung=F
    )


def sample(id, suffix):
    return next(
        x["eingaben"].copy()
        for x in REFS
        if x["fall_id"] == "REF_BIOMETRIEABLAUF_" + id + "_" + suffix
    )


def compare(art, stamp):
    return berechne_regel(
        "AIA_" + art + "_BIOMETRIE_ZEITPUNKT_BIS_FRISTENDE",
        dict(
            biometrie_gepruefter_zeitpunkt=stamp,
            biometrie_qualifiziertes_antragsfristende="2026-10-25T02:00:00+01:00",
        ),
        quellenfassung=F,
    )["wert"]


@pytest.mark.parametrize("art", ["005", "026"])
def test_laufende_grenze_ist_keine_antragstellung(art):
    id = "AIA_" + art + "_BIOMETRIE_ANTRAGSFRISTSTAND"
    d = sample(id, "LAUFEND")
    hours = "24" if art == "005" else "48"
    key = "biometrie_" + hours + "_stunden_frist_zum_stichtag_abgelaufen"
    # Synthetic qualified inclusive end; no raw-hours legal deadline inference.
    d[key] = not compare(art, "2026-10-25T01:00:00Z")
    assert t(id, d)["wert"] is True
    assert d["biometrie_genehmigungsantrag_zum_stichtag_tatsaechlich_gestellt"] is False
    d[key] = not compare(art, "2026-10-25T01:00:00.000001Z")
    assert t(id, d)["wert"] is False
    d["biometrie_" + hours + "_stunden_fristvergleich_rechtlich_qualifiziert"] = False
    assert t(id, d)["status"] == "REGEL_UNGEKLAERT"


def test_abgelehnt_bedeutet_stopp_und_loeschung():
    id = "AIA_005_001_H_LAUFENDER_VERLAUF"
    d = sample(id, "QUALIFIZIERTER_LAUF")
    assert t(id, d)["wert"] is False
    d["genehmigung_abgelehnt"] = True
    assert t(id, d)["wert"] is True
    d.update(
        echtzeiteinsatz_nach_genehmigungsablehnung_sofort_gestoppt=True,
        alle_daten_ergebnisse_und_ausgaben_des_abgelehnten_echtzeiteinsatzes_sofort_verworfen_und_geloescht=False,
    )
    assert t("AIA_005_003_ABLEHNUNG", d)["wert"] is True
    assert t("AIA_005_003_ABLEHNUNGSKRITERIEN", d)["wert"] is False
    post = dict(
        personenbezogene_daten_des_abgelehnten_einsatzes_geloescht=False,
        zur_abgelehnten_genehmigung_gehoeriger_einsatz_sofort_gestoppt=True,
    )
    assert t("AIA_026_010_ABLEHNUNGSKRITERIEN", post)["wert"] is False


def test_registrierung_laufend_ist_nicht_erfuellt_und_fria_bleibt():
    id = "AIA_005_001_H_LAUFENDER_VERLAUF"
    d = sample(id, "QUALIFIZIERTER_LAUF")
    assert t("AIA_005_H_REGISTRIERUNG_LAUFEND", d)["wert"] is True
    assert t("AIA_005_002_REG_NACHWEIS", d)["wert"] is False
    d["grundrechtefolgenabschaetzung_abgeschlossen"] = False
    assert t(id, d)["wert"] is True


def test_vorheriger_antrag_ist_strikt_und_keine_erteilte_genehmigung():
    pre = berechne_regel(
        "AIA_026_010_ANTRAG_VOR_EINSATZ",
        dict(
            biometrie_genehmigungsantrag_zeitpunkt="2026-10-25T02:30:00+02:00",
            nachtraegliche_fernidentifizierung_einsatzbeginn_zeitpunkt="2026-10-25T02:15:00+01:00",
        ),
        quellenfassung=F,
    )
    assert pre["wert"] is True
    d = sample("AIA_026_010_ANTRAG_VOLLZUG", "GESTELLT")
    d["genehmigungsantrag_vor_einsatz"] = pre["wert"]
    d["genehmigungsantrag_unverzueglich_nach_einsatz"] = False
    d["genehmigungsantrag_spaetestens_innerhalb_gesetzlicher_48_stunden"] = False
    assert t("AIA_026_010_ANTRAG_VOLLZUG", d)["wert"] is True
    d["biometrie_genehmigungsantrag_zum_stichtag_tatsaechlich_gestellt"] = False
    assert t("AIA_026_010_ANTRAG_VOLLZUG", d)["wert"] is False
