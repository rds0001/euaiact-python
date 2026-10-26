"""Local Article 2 / substantive rule / 111 / 113 workflows via public APIs.

This example keeps separate legal findings; it does not infer a global approval.
"""

from pathlib import Path
import argparse
from copy import deepcopy
from euaiact import (
    lese_json,
    schreibe_json,
    pruefe_tatbestand,
    pruefe_anwendungsbeginn,
    pruefe_bestandsfrist,
)

_APIS = {
    f.__name__: f
    for f in (pruefe_tatbestand, pruefe_anwendungsbeginn, pruefe_bestandsfrist)
}


def auswerten(daten):
    outputs = []
    for case in daten["faelle"]:
        context = case["kontext"]
        outputs_for_case = []
        for step in case["schritte"]:
            api = step["api"]
            if api not in _APIS:
                raise ValueError("Nicht unterstützte API im Ablauf")
            params = deepcopy(step["parameter"])
            if "stichtag" in params or "quellenfassung" in params:
                raise ValueError(
                    "Stichtag und Quellenfassung stammen ausschliesslich aus dem gemeinsamen Kontext"
                )
            params["quellenfassung"] = context["quellenfassung"]
            if api != "pruefe_tatbestand":
                params["stichtag"] = context["stichtag"]
            outputs_for_case.append(dict(api=api, ergebnis=_APIS[api](**params)))
        outputs.append(
            dict(
                fall_id=case["fall_id"],
                kontext=deepcopy(context),
                schritte=outputs_for_case,
            )
        )
    return outputs


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--daten", type=Path, default=Path(__file__).with_name("geltungsablaeufe.json")
    )
    parser.add_argument("--ausgabe", type=Path, required=True)
    args = parser.parse_args()
    schreibe_json(auswerten(lese_json(args.daten)), args.ausgabe)
