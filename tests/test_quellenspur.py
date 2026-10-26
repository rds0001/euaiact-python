"""Transitive Fundstellen bleiben bei zusammengesetzter Prüfung sichtbar."""

from euaiact import pruefe_tatbestand, regel_info


def test_hochrisikoeinstufung_belegt_anhang_und_ausnahme():
    ergebnis = pruefe_tatbestand("AIA_006_002", {}, quellenfassung="EUAIACT_2026_07_27")
    belege = ergebnis["nachweise"]
    stellen = {b["fundstelle"] for b in belege}
    assert {"ART_006/2", "ART_006/3", "ANH_III/5/b"} <= stellen
    assert len(belege) == len({(b["regel_id"], b["fundstelle"]) for b in belege})
    for beleg in belege:
        assert beleg["regelversion"] == regel_info(beleg["regel_id"])["regelversion"]
    assert any(h.startswith("AIA_006_003_AUSNAHME: ") for h in ergebnis["hinweise"])


def test_gleiche_fundstelle_behaelt_zwei_regelbeziehungen():
    ergebnis = pruefe_tatbestand(
        "AIA_026_008_SPERRE", {}, quellenfassung="EUAIACT_2026_07_27"
    )
    assert [(b["regel_id"], b["fundstelle"]) for b in ergebnis["nachweise"]] == [
        ("AIA_026_008_SPERRE", "ART_026/8"),
        ("AIA_026_008", "ART_026/8"),
    ]
