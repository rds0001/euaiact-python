"""Explizite lokale JSON-Dateien und reine Feldzuordnungen."""

from copy import deepcopy
import json
import math
from pathlib import Path
import re

_MAX_BYTES = 16 * 1024 * 1024
_MAX_GANZZAHL = 9007199254740991


def _lokaler_pfad(pfad):
    if not isinstance(pfad, (str, Path)):
        raise ValueError("Lokaler Dateipfad erforderlich")
    text = str(pfad)
    if not text.strip() or "\x00" in text or text.startswith(("//", "\\\\")):
        raise ValueError("Lokaler Dateipfad erforderlich")
    if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", text) and not re.match(
        r"^[a-zA-Z]:[/\\]", text
    ):
        raise ValueError("URI und URLs sind keine lokalen Dateipfade")
    return Path(text)


def _jsonwert(wert, tiefe=0):
    if tiefe > 100:
        raise ValueError("JSON-Verschachtelung überschreitet 100 Ebenen")
    if wert is None or type(wert) is bool:
        return wert
    if isinstance(wert, str):
        wert.encode("utf-8", errors="strict")
        return wert
    if type(wert) in (int, float):
        if (
            type(wert) is float and (not math.isfinite(wert) or not wert.is_integer())
        ) or abs(wert) > _MAX_GANZZAHL:
            raise ValueError(
                "JSON-Zahlen müssen interoperable ganze Zahlen sein; sonst Text verwenden"
            )
        return int(wert)
    if isinstance(wert, dict):
        if any(not isinstance(k, str) or not k for k in wert):
            raise ValueError("JSON-Objektschlüssel müssen nichtleere Texte sein")
        return {
            _jsonwert(k, tiefe + 1): _jsonwert(v, tiefe + 1) for k, v in wert.items()
        }
    if isinstance(wert, list):
        return [_jsonwert(v, tiefe + 1) for v in wert]
    raise ValueError("Nicht unterstützter JSON-Datentyp")


def _objekt(paare):
    objekt = {}
    for schluessel, wert in paare:
        if schluessel in objekt:
            raise ValueError("Doppelter JSON-Objektschlüssel")
        objekt[schluessel] = wert
    return objekt


def _keine_gebrochene_jsonzahl(text):
    raise ValueError(
        "JSON-Zahlen ohne Bruchteil und Exponent erforderlich; sonst Text verwenden"
    )


def lese_json(pfad):
    """Liest eine lokale UTF-8-Datei; ungültige Austauschdaten: ValueError."""
    with _lokaler_pfad(pfad).open("rb") as datei:
        roh = datei.read(_MAX_BYTES + 1)
    if len(roh) > _MAX_BYTES:
        raise ValueError("JSON-Datei überschreitet 16 MiB")
    try:
        wert = json.loads(
            roh.decode("utf-8"),
            object_pairs_hook=_objekt,
            parse_float=_keine_gebrochene_jsonzahl,
            parse_constant=_keine_gebrochene_jsonzahl,
        )
        return _jsonwert(wert)
    except RecursionError as fehler:
        raise ValueError("JSON-Verschachtelung überschreitet 100 Ebenen") from fehler


def schreibe_json(daten, pfad):
    """Schreibt validierte Daten in eine neue Datei; überschreibt niemals."""
    ziel = _lokaler_pfad(pfad)
    roh = (
        json.dumps(_jsonwert(daten), ensure_ascii=False, indent=2, allow_nan=False)
        + "\n"
    ).encode("utf-8")
    if len(roh) > _MAX_BYTES:
        raise ValueError("JSON-Datei überschreitet 16 MiB")
    with ziel.open("xb") as datei:
        datei.write(roh)


def ordne_daten_zu(datensatz, zuordnung):
    """Ordnet direkte Quellfelder zu; keine Transformation und kein Datei-I/O."""
    if not isinstance(datensatz, dict) or any(
        not isinstance(k, str) or not k for k in datensatz
    ):
        raise ValueError(
            "datensatz muss ein Objekt mit nichtleeren Textschlüsseln sein"
        )
    if not isinstance(zuordnung, dict) or set(zuordnung) != {
        "mappingversion",
        "felder",
    }:
        raise ValueError("Zuordnung benötigt genau mappingversion und felder")
    version, felder = zuordnung["mappingversion"], zuordnung["felder"]
    if (
        not isinstance(version, str)
        or not version.strip()
        or not isinstance(felder, dict)
    ):
        raise ValueError("Ungültige Mappingversion oder Feldzuordnung")
    for ziel, quelle in felder.items():
        if (
            not isinstance(ziel, str)
            or not re.fullmatch(r"[a-z][a-z0-9_]*", ziel)
            or not isinstance(quelle, str)
            or not quelle
        ):
            raise ValueError("Ungültiger Ziel- oder Quellfeldname")
    return {
        "mappingversion": version,
        "eingaben": {
            ziel: deepcopy(datensatz.get(felder[ziel])) for ziel in sorted(felder)
        },
        "herkunft": [
            {
                "zielfeld": ziel,
                "quellfeld": felder[ziel],
                "vorhanden": felder[ziel] in datensatz,
            }
            for ziel in sorted(felder)
        ],
    }
