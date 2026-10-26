"""Allgemeiner Anwendungsbeginn ohne automatische Übergangsentscheidung."""

from functools import lru_cache
from importlib.resources import files
import json

from .fristen import _datum
from .kern import _umschlag


@lru_cache(maxsize=1)
def _zeitkatalog():
    return json.loads(
        files("euaiact")
        .joinpath("resources/anwendungsbeginn.json")
        .read_text(encoding="utf-8")
    )


def pruefe_anwendungsbeginn(bereich, stichtag, *, quellenfassung):
    """Vergleicht Artikel-113-Beginn; Artikel 111 und Geltungsbereich separat."""
    katalog = _zeitkatalog()
    eingaben = {"bereich": bereich, "stichtag": stichtag}
    ergebnis = _umschlag(katalog["regel_id"], eingaben, quellenfassung)
    ergebnis["regelversion"] = katalog["regelversion"]
    if (
        not isinstance(quellenfassung, str)
        or quellenfassung not in katalog["fassungen"]
    ):
        ergebnis["hinweise"] = ["Quellenfassung für diese Regel nicht verfügbar"]
        return ergebnis
    fassung = katalog["fassungen"][quellenfassung]
    fehler = []
    if bereich is not None and (
        not isinstance(bereich, str)
        or bereich
        not in (set(fassung["bereiche"]) | set(fassung.get("offene_bereiche", {})))
    ):
        fehler.append("Bereich in dieser Quellenfassung nicht verfügbar")
    if stichtag is not None:
        try:
            datum = _datum(stichtag)
            if datum < _datum(fassung["fassung_ab"]):
                fehler.append(
                    "Stichtag liegt vor Inkrafttreten der gewählten Quellenfassung"
                )
        except ValueError:
            fehler.append("Ungültiger stichtag")
    if fehler:
        ergebnis["hinweise"] = fehler
        return ergebnis
    fehlend = [name for name, wert in eingaben.items() if wert is None]
    if fehlend:
        ergebnis.update(
            status="EINGABE_FEHLT",
            anwendbarkeit="UNBEKANNT",
            entscheidungsstatus="UNBESTIMMT",
            fehlende_angaben=fehlend,
            entscheidungsrelevante_luecken=fehlend,
        )
        return ergebnis
    if bereich in fassung.get("offene_bereiche", {}):
        frage = fassung["offene_bereiche"][bereich]
        ergebnis.update(
            status="REGEL_UNGEKLAERT",
            anwendbarkeit="UNBEKANNT",
            entscheidungsstatus="UNBESTIMMT",
            entscheidungsschritte=[
                {
                    "operation": "OFFENE_RECHTSFRAGE",
                    "bereich": bereich,
                    "frage_id": frage["frage_id"],
                    "wert": None,
                }
            ],
            hinweise=[frage["hinweis"]],
            nachweise=[
                {
                    "art": "RECHTSQUELLE",
                    "fundstelle": stelle,
                    "quellenfassung": quellenfassung,
                }
                for stelle in frage["fundstellen"]
            ],
        )
        return ergebnis
    beginn = fassung["bereiche"][bereich]
    wert = datum >= _datum(beginn)
    ergebnis.update(
        wert=wert,
        status="AUSGEWERTET",
        anwendbarkeit="UNBEKANNT",
        entscheidungsstatus="ENTSCHIEDEN",
        entscheidungsschritte=[
            {
                "operation": "STICHTAG_AB_BEGINN",
                "bereich": bereich,
                "anwendungsbeginn": beginn,
                "stichtag": stichtag,
                "wert": wert,
            }
        ],
        annahmen=["Ausdrücklich gewählte Quellenfassung und Bereich"],
        hinweise=[
            "Artikel 111 und sachlicher, persönlicher sowie territorialer Geltungsbereich separat prüfen",
            "KAPITEL_I_II_BESTAND schließt Artikel 4a und die neuen Verbote aus",
        ],
        nachweise=[
            {
                "art": "RECHTSQUELLE",
                "fundstelle": "ART_113",
                "quellenfassung": quellenfassung,
            }
        ],
    )
    return ergebnis
