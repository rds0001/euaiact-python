"""Ausschließlich synthetische Unternehmen, identischer Bibliothekscode."""

from pathlib import Path
import argparse
from copy import deepcopy
from euaiact import (
    berechne_regel,
    lese_json,
    ordne_daten_zu,
    pruefe_tatbestand,
    pruefe_stapel,
    pruefe_anwendungsbeginn,
    schreibe_json,
)


def auswerten(pfad):
    daten = lese_json(pfad)
    vorher = deepcopy(daten)
    ergebnisse = []
    for szenario in daten["szenarien"]:
        assert szenario["kennzeichnung"] == "SYNTHETISCH"
        for fall in szenario["faelle"]:
            zugeordnet = ordne_daten_zu(fall["daten"], fall["zuordnung"])
            eingaben = zugeordnet["eingaben"]
            if fall["art"] == "TATBESTAND":
                ergebnis = pruefe_tatbestand(
                    fall["regel_id"], eingaben, quellenfassung=fall["quellenfassung"]
                )
                stapel = pruefe_stapel(
                    [
                        {
                            "fall_id": fall["fall_id"],
                            "regel_id": fall["regel_id"],
                            "eingaben": eingaben,
                        }
                    ],
                    quellenfassung=fall["quellenfassung"],
                )
                assert stapel[0]["ergebnis"] == ergebnis
            elif fall["art"] == "RECHENREGEL":
                ergebnis = berechne_regel(
                    fall["regel_id"], eingaben, quellenfassung=fall["quellenfassung"]
                )
            else:
                assert fall["art"] == "ANWENDUNGSBEGINN"
                ergebnis = pruefe_anwendungsbeginn(
                    **eingaben, quellenfassung=fall["quellenfassung"]
                )
            for feld, wert in fall["erwartung"].items():
                assert ergebnis[feld] == wert, fall["herleitung"]
            ergebnisse.append(
                {
                    "szenario_id": szenario["szenario_id"],
                    "fall_id": fall["fall_id"],
                    "zuordnung": zugeordnet,
                    "ergebnis": ergebnis,
                }
            )
    assert daten == vorher
    return ergebnisse


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--daten",
        type=Path,
        default=Path(__file__).with_name("unternehmen_synthetisch.json"),
    )
    parser.add_argument("--ausgabe", type=Path)
    argumente = parser.parse_args()
    ergebnisse = auswerten(argumente.daten)
    if argumente.ausgabe:
        schreibe_json(ergebnisse, argumente.ausgabe)
    print(f"Synthetische Szenarien: {len(ergebnisse)} Integrationsfälle bestanden")
