"""Versionierte lokale Anhangtabellen, ohne externe Zugriffe."""

from copy import deepcopy
from functools import lru_cache
from importlib.resources import files
import json


@lru_cache(maxsize=1)
def _tabellen():
    daten = json.loads(
        files("euaiact")
        .joinpath("resources/anhangtabellen.json")
        .read_text(encoding="utf-8")
    )
    return {t["tabellen_id"]: t for t in daten["tabellen"]}


def tabellen_katalog():
    """Listet verfügbare Tabellen mit Version, Quellenfassung und Zeilenzahl."""
    return [
        dict(
            tabellen_id=t["tabellen_id"],
            tabellenversion=t["tabellenversion"],
            quellenfassung=t["quellenfassung"],
            bezeichnung=t["bezeichnung"],
            status=t["status"],
            zeilenanzahl=len(t["zeilen"]),
        )
        for t in _tabellen().values()
    ]


def tabelle_info(tabellen_id):
    """Liefert unabhängige Kopie einschließlich Spalten, Zeilen und Quellennachweis.

    Unbekannte oder nicht textuelle ID: KeyError. Kein Schluss auf individuelle
    Anwendbarkeit aus bloßer Tabellenmitgliedschaft.
    """
    if not isinstance(tabellen_id, str) or tabellen_id not in _tabellen():
        raise KeyError("Unbekannte Tabellen-ID")
    return deepcopy(_tabellen()[tabellen_id])
