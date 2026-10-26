"""Qualified limitation timelines; legal uncertainty is not a guessed date."""

from bisect import bisect_right
from calendar import monthrange
from datetime import timedelta

from .fristen import _datum
from .kern import _umschlag

_UNTERBRECHUNGEN = {
    "GPAI_VERFOLGUNG": {
        "DOKUMENTENANFRAGE",
        "MODELLZUGANG",
        "DIALOGEINLADUNG",
        "VERFAHRENSEROEFFNUNG",
        "SONSTIGE_KOMMISSIONSERMITTLUNG",
    },
    "GPAI_VOLLSTRECKUNG": {
        "MITGETEILTE_BETRAGSAENDERUNG",
        "MITGETEILTE_AENDERUNGSABLEHNUNG",
        "KOMMISSIONSVOLLSTRECKUNG",
        "STAATLICHE_VOLLSTRECKUNG_AUF_KOMMISSIONSERSUCHEN",
    },
    "KI_BUERO_VERFOLGUNG": {"FOLGEAKT_75D3_ZU_QUALIFIZIEREN"},
    "KI_BUERO_VOLLSTRECKUNG": {"FOLGEAKT_75D3_ZU_QUALIFIZIEREN"},
}
_HEMMUNGEN = {
    "GPAI_VERFOLGUNG": {"EUGH_ANHAENGIGKEIT"},
    "GPAI_VOLLSTRECKUNG": {
        "ZAHLUNGSAUFSCHUB",
        "EUGH_VOLLSTRECKUNGSHEMMUNG",
        "NATIONALE_GERICHTLICHE_VOLLSTRECKUNGSHEMMUNG",
    },
    "KI_BUERO_VERFOLGUNG": {"FOLGEAKT_75D3_ZU_QUALIFIZIEREN"},
    "KI_BUERO_VOLLSTRECKUNG": {"FOLGEAKT_75D3_ZU_QUALIFIZIEREN"},
}
_KONVENTIONEN = {"EREIGNISTAG", "BEGINNTAG", "VORTAG_DES_BEGINNS"}


class _OffeneKonvention(ValueError):
    pass


class _Kalenderluecke(ValueError):
    pass


def _tag(value):
    try:
        return _datum(value)
    except (ValueError, TypeError):
        raise ValueError("Gueltiges Datum YYYY-MM-DD erforderlich") from None


def _vereinigen(intervalle):
    vereinigt = []
    for a, b in sorted(intervalle):
        if a == b:
            continue
        if vereinigt and a <= vereinigt[-1][1]:
            vereinigt[-1] = (vereinigt[-1][0], max(b, vereinigt[-1][1]))
        else:
            vereinigt.append((a, b))
    return vereinigt


def berechne_verjaehrung(
    verfahren,
    ereignisdatum,
    unterbrechungen,
    hemmungen,
    stichtag,
    *,
    kalender,
    quellenfassung,
    beginnkonvention=None,
    beginnbegruendung=None,
):
    """Evaluate a complete, legally qualified, day-based event record locally.

    GPAI long-period start convention F007 must be explicitly qualified by the
    caller. No1755 interruption rules are applied to the AI Office75c procedure.
    Half-open suspension intervals denote fully qualified whole calendar days.
    A missing interval end denotes an ongoing suspension, not a zero duration.
    """
    inputs = dict(
        verfahren=verfahren,
        ereignisdatum=ereignisdatum,
        unterbrechungen=unterbrechungen,
        hemmungen=hemmungen,
        stichtag=stichtag,
        kalender=kalender,
        beginnkonvention=beginnkonvention,
        beginnbegruendung=beginnbegruendung,
    )
    result = _umschlag("VERJAEHRUNGSVERLAUF", inputs, quellenfassung)
    result.update(regelversion="0.1.0", ergebnistyp="OBJEKT", einheit="KALENDERTAG")
    if quellenfassung != "EUAIACT_2026_07_27":
        result["hinweise"] = ["Quellenfassung fuer diese Regel nicht verfuegbar"]
        return result
    required = (
        "verfahren",
        "ereignisdatum",
        "unterbrechungen",
        "hemmungen",
        "stichtag",
        "kalender",
    )
    missing = [k for k in required if inputs[k] is None]
    if missing:
        result.update(
            status="EINGABE_FEHLT",
            anwendbarkeit="UNBEKANNT",
            entscheidungsstatus="UNBESTIMMT",
            fehlende_angaben=missing,
            entscheidungsrelevante_luecken=missing,
        )
        return result
    try:
        if not isinstance(verfahren, str) or verfahren not in _UNTERBRECHUNGEN:
            raise ValueError("Unzulaessiges Verjaehrungsverfahren")
        start, cutoff = _tag(ereignisdatum), _tag(stichtag)
        if start > cutoff:
            raise ValueError("Ereignisdatum liegt nach Stichtag")
        if (
            type(unterbrechungen) is not list
            or type(hemmungen) is not list
            or max(len(unterbrechungen), len(hemmungen)) > 1000
        ):
            raise ValueError(
                "Ereignisse muessen Listen mit jeweils hoechstens1000 Eintraegen sein"
            )
        if type(kalender) is not dict or set(kalender) != {
            "von",
            "bis",
            "feiertage",
            "bezug",
        }:
            raise ValueError("Kalender benoetigt genau von, bis, feiertage und bezug")
        first, last = _tag(kalender["von"]), _tag(kalender["bis"])
        if (
            first > last
            or not isinstance(kalender["bezug"], str)
            or not kalender["bezug"].strip()
            or type(kalender["feiertage"]) is not list
        ):
            raise ValueError("Ungueltiger Kalender")
        holidays = [_tag(x) for x in kalender["feiertage"]]
        if len(set(holidays)) != len(holidays) or any(
            d < first or d > last for d in holidays
        ):
            raise ValueError("Ungueltige Feiertagsliste")
        holidays = set(holidays)
        resets = []
        for record in unterbrechungen:
            if (
                type(record) is not dict
                or set(record) != {"datum", "art"}
                or not isinstance(record["art"], str)
                or record["art"] not in _UNTERBRECHUNGEN[verfahren]
            ):
                raise ValueError(
                    "Unzulaessiger Unterbrechungseintrag fuer dieses Verfahren"
                )
            day = _tag(record["datum"])
            if day > cutoff:
                raise ValueError("Unterbrechung liegt nach Stichtag")
            resets.append(day)
        intervals, ongoing = [], []
        for index, record in enumerate(hemmungen):
            if (
                type(record) is not dict
                or set(record) != {"von", "bis_exklusiv", "art"}
                or not isinstance(record["art"], str)
                or record["art"] not in _HEMMUNGEN[verfahren]
            ):
                raise ValueError("Unzulaessiger Hemmungseintrag fuer dieses Verfahren")
            a = _tag(record["von"])
            b = (
                cutoff
                if record["bis_exklusiv"] is None
                else _tag(record["bis_exklusiv"])
            )
            if (
                a > cutoff
                or b > cutoff
                or b < a
                or (a == b and record["bis_exklusiv"] is not None)
            ):
                raise ValueError("Ungueltige oder zukuenftige Hemmungsgrenzen")
            intervals.append((a, b))
            if record["bis_exklusiv"] is None:
                ongoing.append((index, a))
        if beginnkonvention is not None and (
            not isinstance(beginnkonvention, str)
            or beginnkonvention not in _KONVENTIONEN
        ):
            raise ValueError("Unzulaessige Beginnkonvention")
        if beginnbegruendung is not None and (
            not isinstance(beginnbegruendung, str) or not beginnbegruendung.strip()
        ):
            raise ValueError("Beginnbegruendung muss nichtleerer Text sein")
        if not verfahren.startswith("GPAI_") and (
            beginnkonvention is not None or beginnbegruendung is not None
        ):
            raise ValueError("1755-Beginnkonvention ist im75c-Verfahren unzulaessig")
    except (ValueError, TypeError, OverflowError) as exc:
        result["hinweise"] = [str(exc)]
        return result

    sources = (
        ["32026R1755/ART_10", "32026R1755/ART_12"]
        if verfahren == "GPAI_VERFOLGUNG"
        else ["32026R1755/ART_11", "32026R1755/ART_12"]
        if verfahren == "GPAI_VOLLSTRECKUNG"
        else ["ART_075c/8", "ART_075d/3"]
    )
    result.update(
        anwendbarkeit="UNBEKANNT",
        nachweise=[
            dict(art="RECHTSQUELLE", fundstelle=s, quellenfassung=quellenfassung)
            for s in sources
        ],
        annahmen=[
            "Vollstaendige lokal qualifizierte Ereignisakte; keine automatische rechtliche Ereigniserkennung",
            "Hemmungen sind halboffene Intervalle qualifizierter ganzer Kalendertage",
            "Ablauf_vor_stichtag bezieht sich auf den Beginn des Stichtagsdatums",
        ],
    )
    if verfahren.startswith("GPAI_") and (
        beginnkonvention is None or beginnbegruendung is None
    ):
        result.update(
            status="REGEL_UNGEKLAERT",
            entscheidungsstatus="UNBESTIMMT",
            hinweise=[
                "F007: Beginn langer1755-Perioden ungeklart; ausdruecklich begruendete Nutzervorgabe erforderlich"
            ],
        )
        return result
    if verfahren.startswith("KI_BUERO_") and (resets or intervals):
        result.update(
            status="REGEL_UNGEKLAERT",
            entscheidungsstatus="UNBESTIMMT",
            hinweise=[
                "Konkrete75d(3)-Folgeregeln fuer Unterbrechung/Hemmung fehlen; keine Uebernahme1755"
            ],
        )
        return result
    if verfahren.startswith("GPAI_"):
        result["nutzervorgaben"] = dict(
            beginnkonvention=beginnkonvention, beginnbegruendung=beginnbegruendung
        )
    convention = beginnkonvention or "EREIGNISTAG"
    merged = _vereinigen(intervals)
    ends = [b for _, b in merged]
    prefix = [0]
    for a, b in merged:
        prefix.append(prefix[-1] + (b - a).days)

    def covered(day):
        index = bisect_right(ends, day)
        total = prefix[index]
        if index < len(merged) and merged[index][0] < day:
            total += (day - merged[index][0]).days
        return total

    def working(day):
        if day < first or day > last:
            raise _Kalenderluecke("Kalender deckt erforderlichen Zeitraum nicht")
        return day.weekday() < 5 and day not in holidays

    def shift(day):
        while not working(day):
            day += timedelta(days=1)
        return day

    def anchor(event):
        if convention == "EREIGNISTAG":
            return event
        begin = shift(event + timedelta(days=1))
        return begin if convention == "BEGINNTAG" else begin - timedelta(days=1)

    def deadline(event, years, horizon):
        origin = anchor(event)
        year = origin.year + years
        if year > 9999:
            raise ValueError("Datumsbereich0001bis9999 ueberschritten")
        raw = origin.replace(
            year=year, day=min(origin.day, monthrange(year, origin.month)[1])
        )
        count_from = origin if convention == "BEGINNTAG" else origin + timedelta(days=1)
        if horizon <= raw:
            raw += timedelta(days=max(0, covered(horizon) - covered(count_from)))
            return shift(raw)
        for a, b in merged:
            if a >= horizon:
                break
            a, b = max(a, count_from), min(b, horizon)
            if b <= a:
                continue
            adjusted = shift(raw)
            if raw < a <= adjusted:
                raise _OffeneKonvention(
                    "Hemmungsbeginn waehrend Endverschiebung: rechtliche Anrechnung offen"
                )
            if a > raw:
                break
            raw += b - a
        return shift(raw)

    try:
        # Validate coverage even for the event-day convention.
        working(start)
        trace, current = [], start
        for event in sorted(set(resets)):
            end = deadline(current, 5, event)
            limit = (
                deadline(start, 10, event) if verfahren == "GPAI_VERFOLGUNG" else None
            )
            effective = min(end, limit) if limit is not None else end
            if event < start:
                state = "VOR_AUSGANGSEREIGNIS_OHNE_NEUSTART"
            elif event > effective:
                state = "NACH_ABLAUF_OHNE_WIEDERBELEBUNG"
            else:
                current = event
                state = "FUENFJAHRESFRIST_NEU"
            trace.append(dict(ereignisdatum=event.isoformat(), wirkung=state))
        end = deadline(current, 5, cutoff)
        limit = deadline(start, 10, cutoff) if verfahren == "GPAI_VERFOLGUNG" else None
        effective = min(end, limit) if limit is not None else end
        relevant_open = [
            i
            for i, a in ongoing
            if a <= effective and cutoff >= a and (limit is None or a <= limit)
        ]
        # The cap and regular clock are both paused by prosecution court stays.
        value = dict(
            verfahren=verfahren,
            letztes_neustartereignis=current.isoformat(),
            regulaeres_fristende=None if relevant_open else end.isoformat(),
            hoechstfristende=None
            if relevant_open or limit is None
            else limit.isoformat(),
            wirksames_fristende=None if relevant_open else effective.isoformat(),
            ablauf_vor_stichtag=False if relevant_open else effective < cutoff,
            laufende_hemmung=bool(relevant_open),
            vereinigte_bekannte_hemmungstage=sum((b - a).days for a, b in merged),
            hemmungs_berechnungsstand_bis_exklusiv=stichtag,
            unterbrechungsschritte=trace,
        )
        gaps = [f"hemmungen[{i}].bis_exklusiv" for i in relevant_open]
        result.update(
            wert=value,
            status="EINGABE_FEHLT" if gaps else "AUSGEWERTET",
            entscheidungsstatus="UNBESTIMMT" if gaps else "ENTSCHIEDEN",
            fehlende_angaben=gaps,
            entscheidungsrelevante_luecken=gaps,
            rechenschritte=[dict(operation="VERJAEHRUNGSVERLAUF", wert=value.copy())],
            hinweise=[
                "Nur unter dokumentierter Ereignis- und Beginnqualifikation; kein behoerdlicher Verjaehrungsbescheid"
            ],
        )
    except _Kalenderluecke as exc:
        result.update(
            status="EINGABE_FEHLT",
            entscheidungsstatus="UNBESTIMMT",
            fehlende_angaben=["kalender.deckung"],
            entscheidungsrelevante_luecken=["kalender.deckung"],
            hinweise=[str(exc)],
        )
    except _OffeneKonvention as exc:
        result.update(
            status="REGEL_UNGEKLAERT",
            entscheidungsstatus="UNBESTIMMT",
            hinweise=[str(exc)],
        )
    except (ValueError, OverflowError) as exc:
        result.update(
            status="EINGABE_UNGUELTIG",
            anwendbarkeit=None,
            entscheidungsstatus=None,
            hinweise=[str(exc)],
        )
    return result
