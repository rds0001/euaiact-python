"""Datumsreferenzen aus dem Fristvertrag, vor Implementierung hergeleitet."""

from copy import deepcopy
import json
from pathlib import Path

import pytest

from euaiact import berechne_frist

REFERENZEN = json.loads(
    (Path(__file__).parent / "fixtures/fristen_referenzen.json").read_text()
)


def berechnen(fall, kalender=None):
    return berechne_frist(
        fall["ereignisdatum"],
        fall["anzahl"],
        fall["einheit"],
        modus=fall["modus"],
        kalender=fall.get("kalender", REFERENZEN["kalender"])
        if kalender is None
        else kalender,
        quellenfassung=REFERENZEN["quellenfassung"],
    )


@pytest.mark.parametrize("fall", REFERENZEN["faelle"], ids=lambda f: f["fall_id"])
def test_fristreferenz(fall):
    ergebnis = berechnen(fall)
    assert ergebnis["status"] == fall.get("status", "AUSGEWERTET")
    assert ergebnis["wert"] == fall["wert"], fall["herleitung"]


def test_feiertag_und_zwei_arbeitstage():
    kalender = deepcopy(REFERENZEN["kalender"])
    kalender["feiertage"] = ["2026-10-26"]
    assert berechnen(REFERENZEN["faelle"][0], kalender)["wert"] == "2026-10-28"


def test_kalenderluecke_verhindert_geratenen_arbeitstag():
    kalender = deepcopy(REFERENZEN["kalender"])
    kalender["bis"] = "2026-10-26"
    ergebnis = berechnen(REFERENZEN["faelle"][0], kalender)
    assert ergebnis["wert"] is None
    assert ergebnis["status"] == "EINGABE_FEHLT"


def test_fester_termin_benoetigt_keinen_kalender():
    ergebnis = berechne_frist(
        "2026-10-23",
        2,
        "TAG",
        modus="FESTER_TERMIN",
        quellenfassung=REFERENZEN["quellenfassung"],
    )
    assert ergebnis["wert"] == "2026-10-25"
    assert ergebnis["fehlende_angaben"] == ["kalender"]
    assert ergebnis["entscheidungsrelevante_luecken"] == []


@pytest.mark.parametrize(
    "datum", ["2026-02-30", "2026-2-1", "2026-01-01\n", "0000-01-01"]
)
def test_keine_datumskorrektur(datum):
    fall = dict(REFERENZEN["faelle"][0], ereignisdatum=datum)
    assert berechnen(fall)["status"] == "EINGABE_UNGUELTIG"


def test_verfahrensmodus_keine_stille_monatsauslegung():
    assert (
        berechne_frist(
            "2026-10-23",
            1,
            "MONAT",
            modus="VERFAHREN_1755_TAGE",
            kalender=REFERENZEN["kalender"],
            quellenfassung=REFERENZEN["quellenfassung"],
        )["status"]
        == "EINGABE_UNGUELTIG"
    )


def test_verfahrensbeginn_benoetigt_kalenderdeckung():
    kalender = dict(REFERENZEN["kalender"], bis="2026-10-25")
    ergebnis = berechne_frist(
        "2026-10-23",
        3,
        "TAG",
        modus="VERFAHREN_1755_TAGE",
        kalender=kalender,
        quellenfassung=REFERENZEN["quellenfassung"],
    )
    assert ergebnis["status"] == "EINGABE_FEHLT"
    assert ergebnis["entscheidungsrelevante_luecken"] == ["kalenderdeckung"]


@pytest.mark.parametrize("einheit", ["TAG", "ARBEITSTAG", "WOCHE", "MONAT", "JAHR"])
def test_rueckwaerts_unterlauf_ist_fehler(einheit):
    kalender = dict(REFERENZEN["kalender"], von="0001-01-01", bis="0001-12-31")
    ergebnis = berechne_frist(
        "0001-01-01",
        1,
        einheit,
        modus="RUECKWAERTS",
        kalender=kalender,
        quellenfassung=REFERENZEN["quellenfassung"],
    )
    assert ergebnis["status"] == "EINGABE_UNGUELTIG"
    assert ergebnis["wert"] is None


def test_rueckwaerts_deckung_und_unveraenderte_eingaben():
    kalender = dict(REFERENZEN["kalender"], von="2026-10-23")
    vorher = deepcopy(kalender)
    ergebnis = berechne_frist(
        "2026-10-26",
        2,
        "TAG",
        modus="RUECKWAERTS",
        kalender=kalender,
        quellenfassung=REFERENZEN["quellenfassung"],
    )
    assert ergebnis["status"] == "EINGABE_FEHLT"
    assert ergebnis["entscheidungsrelevante_luecken"] == ["kalenderdeckung"]
    assert kalender == vorher


def test_rueckwaerts_mindesttage_duerfen_nicht_unterlaufen():
    kalender = dict(
        REFERENZEN["kalender"],
        von="0001-01-01",
        bis="0001-12-31",
        feiertage=["0001-01-01", "0001-01-02"],
    )
    ergebnis = berechne_frist(
        "0001-01-03",
        2,
        "TAG",
        modus="RUECKWAERTS",
        kalender=kalender,
        quellenfassung=REFERENZEN["quellenfassung"],
    )
    assert ergebnis["status"] == "EINGABE_UNGUELTIG"
