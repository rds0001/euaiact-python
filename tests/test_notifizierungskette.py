"""Calendar expiry and an actual current designation are separate inputs."""

import json
from pathlib import Path
from euaiact import berechne_regel, berechne_frist, pruefe_tatbestand

F = "EUAIACT_2026_07_27"


def test_taetigkeit_am_fristtag_und_nach_abgeschlossener_einwandsperiode():
    cases = json.loads(
        (Path(__file__).parent / "fixtures/grundregeln_referenzen.json").read_text()
    )["faelle"]
    base = next(
        f["eingaben"]
        for f in cases
        if f["fall_id"] == "REF_NOTIFIZIERUNGSKETTE_GESAMT_JA"
    )
    period = berechne_regel(
        "AIA_030_EINWANDSPERIODE",
        dict(notifizierungsgrundlage="AKKREDITIERUNGSBESCHEINIGUNG"),
        quellenfassung=F,
    )["wert"]
    end = berechne_frist(
        "2026-10-23",
        period["anzahl"],
        period["einheit"],
        modus="FRIST",
        kalender=dict(
            von="2026-10-01",
            bis="2026-12-31",
            feiertage=["2026-11-06"],
            bezug="SYNTHETISCH",
        ),
        quellenfassung=F,
    )["wert"]
    assert end == "2026-11-09"
    # Evaluation at the BEGINNING of each stated day; expiry is at the end of end.
    for day, expected in [("2026-11-09", False), ("2026-11-10", True)]:
        result = pruefe_tatbestand(
            "AIA_030_TAETIGKEITSWEG",
            base | dict(einschlaegige_einwandsperiode_abgelaufen=day > end),
            quellenfassung=F,
        )
        assert result["wert"] is expected
    withdrawn = pruefe_tatbestand(
        "AIA_030_TAETIGKEITSWEG",
        base
        | dict(
            konkrete_stellenbenennung_fuer_betrachtete_taetigkeit_aktuell_wirksam=False
        ),
        quellenfassung=F,
    )
    assert withdrawn["wert"] is False
