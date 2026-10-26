"""Strukturierte sachliche Pflichtauslösung ohne Erfüllungs- oder Gesamturteil."""

from copy import deepcopy
from functools import lru_cache
from importlib.resources import files
import json

from .kern import _umschlag, pruefe_tatbestand


@lru_cache(maxsize=1)
def _pflichtendaten():
    daten = json.loads(
        files("euaiact")
        .joinpath("resources/pflichten.json")
        .read_text(encoding="utf-8")
    )
    return {p["pflicht_id"]: p for p in daten["pflichten"]}


def pflicht_katalog():
    """Liefert den verfügbaren Teilkatalog als unabhängige native Datensätze."""
    return deepcopy(list(_pflichtendaten().values()))


def ermittle_pflicht(pflicht_id, eingaben, *, quellenfassung):
    """Verknüpft geprüften sachlichen Auslöser mit seiner bedingten Rechtsfolge."""
    if not isinstance(pflicht_id, str) or pflicht_id not in _pflichtendaten():
        ergebnis = _umschlag(None, eingaben, quellenfassung)
        ergebnis.update(ergebnistyp="OBJEKT", hinweise=["Unbekannte Pflicht-ID"])
        return ergebnis
    pflicht = _pflichtendaten()[pflicht_id]
    ergebnis = pruefe_tatbestand(
        pflicht["ausloeser_regel"], eingaben, quellenfassung=quellenfassung
    )
    ergebnis["ergebnistyp"] = "OBJEKT"
    if ergebnis["status"] == "EINGABE_UNGUELTIG":
        return ergebnis
    ausgeloest = ergebnis["wert"]
    ergebnis["wert"] = {
        **{
            k: deepcopy(pflicht[k])
            for k in (
                "pflicht_id",
                "pflichtversion",
                "adressat",
                "gegenstand",
                "ausnahmen",
                "fundstellen",
                "fristregel_ids",
                "rechtsfolge",
                "zeitbezug",
                "nachweisanforderungen",
                "erfuellungskriterien",
            )
        },
        "ausloeser_erfuellt": ausgeloest,
        "erfuellung": "NICHT_GEPRUEFT",
    }
    ergebnis["hinweise"].extend(
        [
            "Bedingte Rechtsfolge; Erfüllung und allgemeine Anwendbarkeit nicht geprüft",
            "Pflichtkatalogstatus: " + pflicht["status"],
            pflicht["automatisierungsgrenze"],
        ]
    )
    return ergebnis
