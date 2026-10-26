"""Deterministische Dreiwertlogik und exakte Vergleiche, ohne externes I/O."""

from copy import deepcopy
from decimal import Decimal
from functools import lru_cache
from importlib.resources import files
import json
import re

from .zeitpunkte import _kalenderdatum, ZEITPUNKTMUSTER, _zeitpunktteile


@lru_cache(maxsize=1)
def _katalog():
    daten = json.loads(
        files("euaiact").joinpath("resources/regeln.json").read_text(encoding="utf-8")
    )
    rechenregeln = json.loads(
        files("euaiact")
        .joinpath("resources/rechenregeln.json")
        .read_text(encoding="utf-8")
    )
    for regel in rechenregeln["regeln"]:
        regel["quellenfassung"] = rechenregeln["quellenfassung"]
        regel["status"] = rechenregeln["status"]
    return {
        regel["regel_id"]: regel for regel in daten["regeln"] + rechenregeln["regeln"]
    }


def regel_info(regel_id):
    """Liefert eine unabhängige Kopie der Spezifikation; unbekannte ID: KeyError."""
    if not isinstance(regel_id, str) or regel_id not in _katalog():
        raise KeyError("Unbekannte Regel-ID")
    return deepcopy(_katalog()[regel_id])


def regel_katalog():
    """Liefert die mitgelieferten Regeln mit Quellenfassung und Prüfstatus."""
    return [
        {
            name: regel[name]
            for name in (
                "regel_id",
                "regelversion",
                "bezeichnung",
                "quellenfassung",
                "status",
            )
        }
        for regel in _katalog().values()
    ]


def schema_info(schema_id="ERGEBNIS_0_1_0"):
    """Liest das mitgelieferte JSON-Schema; keine Remote-Auflösung."""
    if isinstance(schema_id, str) and schema_id.endswith(":EINGABEN"):
        vertrag = eingabevertrag(schema_id[:-9])
        eigenschaften = {}
        for name, feld in vertrag["felder"].items():
            typ = feld["typ"]
            if typ == "BOOLEAN":
                domain = {"type": "boolean"}
            elif typ == "ENUM":
                domain = {"type": "string", "enum": deepcopy(feld["werte"])}
            elif typ == "ENUMMENGE":
                domain = {
                    "type": "array",
                    "items": {"type": "string", "enum": deepcopy(feld["werte"])},
                    "uniqueItems": True,
                    "maxItems": len(feld["werte"]),
                }
            elif typ == "NATURZAHLTEXT":
                domain = {
                    "type": "string",
                    "pattern": r"^(0|[1-9][0-9]*)$(?![\s\S])",
                    "maxLength": 256,
                    "description": "Nichtnegative ganze Zahl als kanonischer Zifferntext; Nennerminimum prueft der native Kern.",
                }
                if "minimum" in feld:
                    domain["x-euaiact-minimum"] = feld["minimum"]
            elif typ == "DATUM":
                domain = {
                    "type": "string",
                    "pattern": r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$(?![\s\S])",
                    "maxLength": 10,
                    "description": "Gregorianisches Datum YYYY-MM-DD, Jahre 0001-9999; Kalendergueltigkeit prueft der native Kern.",
                }
            elif typ == "DATUMZEIT":
                domain = {
                    "type": "string",
                    "pattern": ZEITPUNKTMUSTER,
                    "maxLength": 32,
                    "description": "Expliziter Offset, Jahre 0001–9999, maximal sechs Nachkommastellen; Kalendergueltigkeit und Offset prueft der native Kern.",
                }
            elif typ == "GANZZAHL":
                domain = {"type": "integer"}
                for grenze in ("minimum", "maximum"):
                    if grenze in feld:
                        domain[grenze] = int(feld[grenze])
            elif typ == "DEZIMAL":
                domain = {
                    "type": "string",
                    "pattern": r"^-?(0|[1-9][0-9]*)(\.[0-9]+)?$(?![\s\S])",
                    "maxLength": 4096,
                    "description": "Exakte Dezimalgrenzen prueft die native Regelauswertung.",
                }
                for grenze in ("minimum", "maximum"):
                    if grenze in feld:
                        domain["x-euaiact-" + grenze] = feld[grenze]
            else:
                raise ValueError("Unbekannter interner Feldtyp")
            eigenschaften[name] = {"anyOf": [{"type": "null"}, domain]}
            for quelle, ziel in (
                ("definition", "description"),
                ("herkunft", "x-euaiact-herkunft"),
                ("bezugszeit", "x-euaiact-bezugszeit"),
            ):
                if quelle in feld:
                    eigenschaften[name][ziel] = feld[quelle]
        return {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": "urn:euaiact:" + schema_id,
            "type": "object",
            "additionalProperties": False,
            "properties": eigenschaften,
        }
    if schema_id != "ERGEBNIS_0_1_0":
        raise KeyError("Unbekannte Schema-ID")
    return json.loads(
        files("euaiact")
        .joinpath("resources/ergebnis.schema.json")
        .read_text(encoding="utf-8")
    )


@lru_cache(maxsize=512)
def _felder(regel_id, pfad=()):
    if regel_id in pfad:
        raise RuntimeError("Zyklischer paketinterner Regelverweis")
    regel = _katalog()[regel_id]
    felder = dict(regel["eingaben"])

    def besuchen(knoten):
        if "regel" in knoten:
            weitere = _felder(knoten["regel"], pfad + (regel_id,))
            for name, vertrag in weitere.items():
                if name in felder and felder[name] != vertrag:
                    raise RuntimeError("Widersprüchlicher paketinterner Feldvertrag")
                felder[name] = vertrag
        for argument in knoten.get("argumente", []):
            besuchen(argument)

    besuchen(regel["ausdruck"])
    return felder


def eingabevertrag(regel_id):
    """Vollständige Feldverträge einschließlich transitiver Regelverweise."""
    regel = regel_info(regel_id)
    felder = _felder(regel_id) if "ausdruck" in regel else regel["eingaben"]
    return {
        "regel_id": regel_id,
        "regelversion": regel["regelversion"],
        "quellenfassung": regel["quellenfassung"],
        "schemaversion": "0.1.0",
        "felder": {name: deepcopy(felder[name]) for name in sorted(felder)},
        "unbekannt": "Fehlende Felder und null bleiben unbekannt; keine stillen Defaults",
        "zusaetzliche_felder": "UNZULAESSIG",
    }


def _ganze_zahl(wert):
    """Finite native integer value within the interoperable exact range."""
    return (
        type(wert) in (int, float)
        and -9007199254740991 <= wert <= 9007199254740991
        and (type(wert) is int or wert.is_integer())
    )


def _normalisierte_ganzzahlen(eingaben, felder):
    # Called only after validation; never coerce decimal/rational text or booleans.
    return {
        k: int(v) if v is not None and felder[k]["typ"] == "GANZZAHL" else v
        for k, v in eingaben.items()
    }


def _fehler(eingaben, felder):
    fehler = []
    if not isinstance(eingaben, dict) or any(not isinstance(k, str) for k in eingaben):
        return ["eingaben muss ein Dictionary mit Textschlüsseln sein"]
    for name, wert in eingaben.items():
        if name not in felder:
            fehler.append(f"Unbekanntes Eingabefeld: {name}")
            continue
        if wert is None:
            continue
        vertrag = felder[name]
        if vertrag["typ"] == "BOOLEAN":
            if type(wert) is not bool:
                fehler.append(f"Boolean oder null erforderlich: {name}")
        elif vertrag["typ"] == "DEZIMAL":
            if (
                not isinstance(wert, str)
                or len(wert) > 4096
                or not re.fullmatch(r"-?(0|[1-9][0-9]*)(\.[0-9]+)?", wert)
            ):
                fehler.append(f"Kanonische Dezimalzeichenfolge erforderlich: {name}")
            elif "minimum" in vertrag and Decimal(wert) < Decimal(vertrag["minimum"]):
                fehler.append(f"Unter Minimum: {name}")
            elif "maximum" in vertrag and Decimal(wert) > Decimal(vertrag["maximum"]):
                fehler.append(f"Über Maximum: {name}")
        elif vertrag["typ"] == "ENUM":
            if not isinstance(wert, str) or wert not in vertrag["werte"]:
                fehler.append(f"Unzulässige Kategorie: {name}")
        elif vertrag["typ"] == "ENUMMENGE":
            if (
                not isinstance(wert, list)
                or len(wert) > len(vertrag["werte"])
                or any(
                    not isinstance(x, str) or x not in vertrag["werte"] for x in wert
                )
                or len(set(wert)) != len(wert)
            ):
                fehler.append(
                    f"Eindeutige Liste zulässiger Kategorien erforderlich: {name}"
                )
        elif vertrag["typ"] == "NATURZAHLTEXT":
            if (
                not isinstance(wert, str)
                or len(wert) > 256
                or not re.fullmatch(r"0|[1-9][0-9]*", wert)
            ):
                fehler.append(
                    f"Kanonischer Ganzzahltext mit maximal256Stellen erforderlich: {name}"
                )
            elif int(wert) < int(vertrag.get("minimum", "0")):
                fehler.append(f"Ganzzahltext unter dem erlaubten Minimum: {name}")
        elif vertrag["typ"] == "DATUM":
            try:
                _kalenderdatum(wert)
            except ValueError:
                fehler.append(
                    f"Gueltiges Kalenderdatum YYYY-MM-DD erforderlich: {name}"
                )
        elif vertrag["typ"] == "DATUMZEIT":
            try:
                _zeitpunktteile(wert)
            except ValueError:
                fehler.append(
                    f"Gueltiger Zeitpunkt mit explizitem Offset erforderlich: {name}"
                )
        elif vertrag["typ"] == "GANZZAHL":
            if not _ganze_zahl(wert):
                fehler.append(f"Ganze Zahl erforderlich: {name}")
            elif wert < int(vertrag["minimum"]) or wert > int(vertrag["maximum"]):
                fehler.append(f"Außerhalb Wertebereich: {name}")
        else:
            raise RuntimeError("Unbekannter paketinterner Feldtyp")
    return fehler


def _umschlag(regel_id, eingaben, quellenfassung):
    return {
        "wert": None,
        "ergebnistyp": "WAHRHEITSWERT",
        "einheit": None,
        "status": "EINGABE_UNGUELTIG",
        "anwendbarkeit": None,
        "entscheidungsstatus": None,
        "regel_id": regel_id if isinstance(regel_id, str) else None,
        "regelversion": None,
        "quellenfassung": quellenfassung if isinstance(quellenfassung, str) else None,
        "schemaversion": "0.1.0",
        "eingaben": deepcopy(eingaben)
        if isinstance(eingaben, dict) and all(isinstance(k, str) for k in eingaben)
        else {},
        "nutzervorgaben": {},
        "entscheidungsschritte": [],
        "rechenschritte": [],
        "annahmen": [],
        "hinweise": [],
        "fehlende_angaben": [],
        "entscheidungsrelevante_luecken": [],
        "nachweise": [],
    }


def pruefe_tatbestand(regel_id, eingaben, *, quellenfassung):
    """Prüft einen sachlichen Tatbestand anhand ausdrücklich übergebener Fakten.

    Die Funktion prüft weder den Zeitbezug noch die allgemeine Rechtmäßigkeit.
    Deshalb bleibt die rechtliche Anwendbarkeit UNBEKANNT. Decimal-Zeichenfolgen
    werden ohne Rundung verglichen. Auch logisch irrelevante Werte werden validiert.
    """
    ergebnis = _umschlag(regel_id, eingaben, quellenfassung)
    if not isinstance(regel_id, str) or regel_id not in _katalog():
        ergebnis["hinweise"] = ["Unbekannte Regel-ID"]
        return ergebnis
    regel = _katalog()[regel_id]
    ergebnis["regelversion"] = regel["regelversion"]
    if "ausdruck" not in regel:
        ergebnis["hinweise"] = ["Rechenregel erfordert berechne_regel"]
        return ergebnis
    if quellenfassung != regel["quellenfassung"]:
        ergebnis["hinweise"] = ["Quellenfassung für diese Regel nicht verfügbar"]
        return ergebnis
    felder = _felder(regel_id)
    fehler = _fehler(eingaben, felder)
    if fehler:
        ergebnis["hinweise"] = fehler
        return ergebnis
    eingaben = _normalisierte_ganzzahlen(eingaben, felder)
    ergebnis["eingaben"] = deepcopy(eingaben)
    fehlend = {name for name in felder if eingaben.get(name) is None}
    schritte = []
    beteiligte = [regel_id]
    rechtsfragen = {}

    def datenluecken(luecken):
        return sorted(x for x in luecken if not x.startswith("RECHTSFRAGE:"))

    def fragen(luecken):
        return sorted(
            x.split(":", 1)[1] for x in luecken if x.startswith("RECHTSFRAGE:")
        )

    def auswerten(knoten, kennung, pfad="0"):
        if "rechtsfrage" in knoten:
            frage = knoten["rechtsfrage"]
            rechtsfragen[frage] = knoten["hinweis"]
            schritte.append(
                {
                    "schritt": len(schritte) + 1,
                    "regel_id": kennung,
                    "bedingung_id": kennung + ":K" + pfad,
                    "operator": "OFFENE_RECHTSFRAGE",
                    "frage_id": frage,
                    "wert": None,
                    "entscheidungsrelevante_luecken": [],
                    "offene_rechtsfragen": [frage],
                }
            )
            return None, {"RECHTSFRAGE:" + frage}
        if "feld" in knoten:
            name = knoten["feld"]
            wert = eingaben.get(name)
            schritte.append(
                {
                    "schritt": len(schritte) + 1,
                    "regel_id": kennung,
                    "bedingung_id": kennung + ":K" + pfad,
                    "operator": "EINGABEFELD",
                    "eingabefeld": name,
                    "wert": wert,
                    "entscheidungsrelevante_luecken": [name] if wert is None else [],
                }
            )
            if wert is None:
                return None, {name}
            return (Decimal(wert) if felder[name]["typ"] == "DEZIMAL" else wert), set()
        if "dezimal" in knoten:
            return Decimal(knoten["dezimal"]), set()
        if "text" in knoten:
            return knoten["text"], set()
        if "menge" in knoten:
            return knoten["menge"], set()
        if "regel" in knoten:
            ziel = knoten["regel"]
            if ziel not in beteiligte:
                beteiligte.append(ziel)
            return auswerten(_katalog()[ziel]["ausdruck"], ziel)
        paare = [
            auswerten(argument, kennung, pfad + "." + str(index))
            for index, argument in enumerate(knoten["argumente"])
        ]
        werte = [paar[0] for paar in paare]
        luecken = set().union(*(paar[1] for paar in paare))
        op = knoten["op"]
        if op == "UND":
            wert = (
                False
                if any(w is False for w in werte)
                else None
                if any(w is None for w in werte)
                else True
            )
        elif op == "ODER":
            wert = (
                True
                if any(w is True for w in werte)
                else None
                if any(w is None for w in werte)
                else False
            )
        elif op == "NICHT":
            wert = None if werte[0] is None else not werte[0]
        elif op == "TEILMENGE":
            wert = (
                None
                if any(w is None for w in werte)
                else set(werte[0]).issubset(werte[1])
            )
        elif op == "GLEICH":
            wert = None if any(w is None for w in werte) else werte[0] == werte[1]
        elif op in {"GROESSER", "GROESSER_GLEICH", "KLEINER_GLEICH"}:
            if any(w is None for w in werte):
                wert = None
            elif op == "GROESSER":
                wert = werte[0] > werte[1]
            elif op == "GROESSER_GLEICH":
                wert = werte[0] >= werte[1]
            else:
                wert = werte[0] <= werte[1]
        else:
            raise RuntimeError("Unbekannter paketinterner Operator")
        if wert is not None:
            luecken = set()
        schritte.append(
            {
                "schritt": len(schritte) + 1,
                "regel_id": kennung,
                "bedingung_id": kennung + ":K" + pfad,
                "operator": op,
                "wert": wert,
                "entscheidungsrelevante_luecken": datenluecken(luecken),
            }
        )
        if fragen(luecken):
            schritte[-1]["offene_rechtsfragen"] = fragen(luecken)
        return wert, luecken

    wert, luecken = auswerten(regel["ausdruck"], regel_id)
    schritte.append(
        {
            "schritt": len(schritte) + 1,
            "regel_id": regel_id,
            "operator": "REGELERGEBNIS",
            "wert": wert,
            "entscheidungsrelevante_luecken": datenluecken(luecken),
        }
    )
    if fragen(luecken):
        schritte[-1]["offene_rechtsfragen"] = fragen(luecken)
    ergebnis.update(
        {
            "wert": wert,
            "status": "REGEL_UNGEKLAERT"
            if fragen(luecken)
            else "EINGABE_FEHLT"
            if wert is None
            else "AUSGEWERTET",
            "anwendbarkeit": "UNBEKANNT",
            "entscheidungsstatus": "UNBESTIMMT" if wert is None else "ENTSCHIEDEN",
            "entscheidungsschritte": schritte,
            "fehlende_angaben": sorted(fehlend),
            "entscheidungsrelevante_luecken": datenluecken(luecken),
            "annahmen": [
                "Sachlicher Tatbestand; zeitliche und allgemeine rechtliche Anwendbarkeit separat prüfen",
                "Katalogstatus: " + regel["status"],
            ],
            "hinweise": [regel["automatisierungsgrenze"]]
            + [
                "Offene Rechtsfrage " + frage + ": " + rechtsfragen[frage]
                for frage in fragen(luecken)
            ]
            + [
                kennung + ": " + _katalog()[kennung]["automatisierungsgrenze"]
                for kennung in beteiligte[1:]
            ],
            "nachweise": [
                {
                    "art": "RECHTSQUELLE",
                    "fundstelle": stelle,
                    "quellenfassung": quellenfassung,
                    "regel_id": kennung,
                    "regelversion": _katalog()[kennung]["regelversion"],
                }
                for kennung in beteiligte
                for stelle in _katalog()[kennung]["fundstellen"]
            ],
        }
    )
    return ergebnis


def pruefe_stapel(faelle, *, quellenfassung):
    """Prüft getrennte Fälle; ungültige oder doppelte Fall-IDs: ValueError."""
    if not isinstance(faelle, list):
        raise ValueError("faelle muss eine Liste sein")
    kennungen = set()
    for fall in faelle:
        if not isinstance(fall, dict) or set(fall) != {
            "fall_id",
            "regel_id",
            "eingaben",
        }:
            raise ValueError("Jeder Fall benötigt genau fall_id, regel_id und eingaben")
        kennung = fall["fall_id"]
        if not isinstance(kennung, str) or not kennung.strip() or kennung in kennungen:
            raise ValueError("Fall-IDs müssen nichtleere, eindeutige Texte sein")
        kennungen.add(kennung)
    return [
        {
            "fall_id": fall["fall_id"],
            "ergebnis": pruefe_tatbestand(
                fall["regel_id"], fall["eingaben"], quellenfassung=quellenfassung
            ),
        }
        for fall in faelle
    ]
