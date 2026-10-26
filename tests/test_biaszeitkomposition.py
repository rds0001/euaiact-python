"""A positive substantive test cannot settle the unresolved application date."""

from euaiact import pruefe_tatbestand, pruefe_anwendungsbeginn, eingabevertrag

F = "EUAIACT_2026_07_27"


def test_positive_schutzvoraussetzungen_loesen_keine_zeitfreigabe_aus():
    rid = "AIA_004A_001_VORAUSSETZUNGEN"
    data = dict.fromkeys(eingabevertrag(rid)["felder"], True)
    substance = pruefe_tatbestand(rid, data, quellenfassung=F)
    timing = pruefe_anwendungsbeginn("ARTIKEL_4A", "2026-10-25", quellenfassung=F)
    assert substance["wert"] is True
    assert substance["anwendbarkeit"] == "UNBEKANNT"
    assert timing["status"] == "REGEL_UNGEKLAERT" and timing["wert"] is None


def test_loeschanlass_ist_keine_datenschutzfreigabe():
    result = pruefe_tatbestand(
        "AIA_004A_LOESCHUNG",
        dict(
            besondere_personendaten_fuer_biaspruefung_verarbeitet=True,
            bias_korrektur_abgeschlossen=False,
            aufbewahrungszeitraum_besonderer_daten_beendet=True,
        ),
        quellenfassung=F,
    )
    assert result["wert"] is True and result["anwendbarkeit"] == "UNBEKANNT"
