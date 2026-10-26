"""All GPAI delegations use the original cohort and preserve actual revocation."""

import json
from pathlib import Path
from euaiact import berechne_regel, berechne_frist, pruefe_tatbestand

F = "EUAIACT_2026_07_27"


def test_gpai_kohorte_ist_keine_widerrufsfreistellung():
    cases = json.loads(
        (Path(__file__).parent / "fixtures/grundregeln_referenzen.json").read_text()
    )["faelle"]
    period = berechne_regel("AIA_097_002_DELEGATIONSDAUER", {}, quellenfassung=F)[
        "wert"
    ]
    end = berechne_frist(
        "2024-08-01",
        period["anzahl"],
        period["einheit"],
        modus="FESTER_TERMIN",
        quellenfassung=F,
    )
    assert end["wert"] == "2029-08-01"
    for suffix in ["051_003", "052_004", "053_005", "053_006"]:
        data = next(
            x["eingaben"]
            for x in cases
            if x["fall_id"] == "REF_GPAIDELEGATION_" + suffix + "_WEG_JA"
        )
        # Although the qualified period is current, the actual revocation wins.
        result = pruefe_tatbestand(
            "AIA_" + suffix + "_DELEGATIONSWEG",
            data | dict(widerrufsentscheidung_ist_zum_pruefzeitpunkt_wirksam=True),
            quellenfassung=F,
        )
        assert result["wert"] is False
