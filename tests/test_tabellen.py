"""Handverfasste Quellen-/Integrationsgrenzen der Anhangtabellen."""

import pytest
from euaiact import tabellen_katalog, tabelle_info


def test_umfang_und_fassungen():
    assert {t["tabellen_id"]: t["zeilenanzahl"] for t in tabellen_katalog()} == {
        "ANH_I": 20,
        "ANH_II": 16,
        "ANH_X": 12,
        "ANH_XIII": 7,
        "ANH_XIV": 22,
    }
    assert all(t["quellenfassung"] == "EUAIACT_2026_07_27" for t in tabellen_katalog())


def test_maschinen_und_luftfahrt_reichweite():
    rows = tabelle_info("ANH_I")["zeilen"]
    assert not any(r["nummer"] == 1 or r["celex"] == "32006L0042" for r in rows)
    machine = next(r for r in rows if r["celex"] == "32023R1230")
    assert (machine["nummer"], machine["abschnitt"]) == (21, "B")
    air = next(r for r in rows if r["nummer"] == 20)
    assert (
        "unbemannte" in air["reichweite"]
        and "Fernsteuerungsausrüstung" in air["reichweite"]
    )


def test_codes_und_it_systeme():
    codes = {r["code"]: r for r in tabelle_info("ANH_XIV")["zeilen"]}
    assert "AIP 0101" not in codes
    assert codes["AIP 0111"]["zuordnung"] == "ANH_I/11"
    assert codes["AIB 0203"]["zuordnung"] == "ANH_III/1/c"
    assert "AIH 0401" in codes["AIH 0205"]["systemtyp"]
    assert "agentischer KI" in codes["AIH 0401"]["systemtyp"]
    eurodac = next(r for r in tabelle_info("ANH_X")["zeilen"] if r["gruppe"] == 3)
    assert eurodac["celex"] == "32024R1358"


def test_keine_globalen_erlaubnisse_und_keine_mutation():
    t = tabelle_info("ANH_II")
    assert "zuvor aufgeführten" in t["zeilen"][-1]["deliktsgruppe"]
    t["zeilen"][0]["deliktsgruppe"] = "VERAENDERT"
    t["grenzen"].clear()
    assert tabelle_info("ANH_II")["zeilen"][0]["deliktsgruppe"] == "Terrorismus"
    assert tabelle_info("ANH_II")["grenzen"]
    k = tabellen_katalog()
    k[0]["zeilenanzahl"] = 0
    assert tabellen_katalog()[0]["zeilenanzahl"] == 20


@pytest.mark.parametrize("kennung", [None, True, [], {}, 1, "", "ANH_III", "anh_i"])
def test_ungueltige_kennung(kennung):
    with pytest.raises(KeyError, match="Unbekannte Tabellen-ID"):
        tabelle_info(kennung)
