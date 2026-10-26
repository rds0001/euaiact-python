"""Native Offline-Regelprüfung zum EU AI Act; fachlicher Entwicklungsstand."""

from .kern import (
    pruefe_stapel,
    pruefe_tatbestand,
    regel_info,
    regel_katalog,
    eingabevertrag,
    schema_info,
)
from .rechnen import berechne_bussgeldobergrenze, berechne_regel
from .fristen import berechne_frist
from .unternehmensgruppe import aggregiere_unternehmensgruppe
from .periodenfristen import berechne_periodenfrist
from .verjaehrung import berechne_verjaehrung
from .daten import lese_json, schreibe_json, ordne_daten_zu
from .zeit import pruefe_anwendungsbeginn
from .bestand import pruefe_bestandsfrist
from .pflichten import pflicht_katalog, ermittle_pflicht
from .tabellen import tabellen_katalog, tabelle_info

__all__ = [
    "aggregiere_unternehmensgruppe",
    "berechne_periodenfrist",
    "berechne_verjaehrung",
    "tabellen_katalog",
    "tabelle_info",
    "pflicht_katalog",
    "ermittle_pflicht",
    "pruefe_bestandsfrist",
    "schema_info",
    "eingabevertrag",
    "pruefe_anwendungsbeginn",
    "lese_json",
    "schreibe_json",
    "ordne_daten_zu",
    "berechne_frist",
    "berechne_bussgeldobergrenze",
    "berechne_regel",
    "pruefe_stapel",
    "pruefe_tatbestand",
    "regel_info",
    "regel_katalog",
]
__version__ = "0.1.0"
