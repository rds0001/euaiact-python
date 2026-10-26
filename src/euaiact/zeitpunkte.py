"""Explizite Offset-Zeitpunkte, ohne Systemzeitzone oder Gleitkomma-Bruchteile."""

from datetime import date
import re

ZEITPUNKTMUSTER = (
    r"^([0-9]{4})-([0-9]{2})-([0-9]{2})T([0-9]{2}):([0-9]{2}):([0-9]{2})"
    r"(?:\.([0-9]{1,6}))?(Z|[+-][0-9]{2}:[0-9]{2})$(?![\s\S])"
)


def _zeitpunktteile(wert):
    """UTC-Ganzsekunden seit 0001-01-01 und separate Mikrosekunden."""
    if not isinstance(wert, str) or len(wert) > 32:
        raise ValueError("Ungueltiger Zeitpunkt")
    match = re.fullmatch(ZEITPUNKTMUSTER, wert)
    if match is None:
        raise ValueError("Ungueltiger Zeitpunkt")
    jahr, monat, tag, stunde, minute, sekunde = map(int, match.groups()[:6])
    datum = date(jahr, monat, tag)
    if stunde > 23 or minute > 59 or sekunde > 59:
        raise ValueError("Ungueltige Uhrzeit")
    zone = match[8]
    offset = 0
    if zone != "Z":
        oh, om = int(zone[1:3]), int(zone[4:6])
        if oh > 23 or om > 59 or zone == "-00:00":
            raise ValueError("Ungueltiger oder unbekannter Offset")
        offset = (oh * 3600 + om * 60) * (1 if zone[0] == "+" else -1)
    ganz = (
        (datum.toordinal() - 1) * 86400 + stunde * 3600 + minute * 60 + sekunde - offset
    )
    mikro = int((match[7] or "").ljust(6, "0"))
    return ganz, mikro


def _kalenderdatum(wert):
    """Strict local civil date; no timezone or machine-date inference."""
    if not isinstance(wert, str) or not re.fullmatch(
        r"[0-9]{4}-[0-9]{2}-[0-9]{2}", wert
    ):
        raise ValueError("Ungueltiges Kalenderdatum")
    return date.fromisoformat(wert)
