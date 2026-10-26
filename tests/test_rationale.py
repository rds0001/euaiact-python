"""Exact fractions must survive adapters, independent decimal contexts and reuse."""

from copy import deepcopy
from decimal import localcontext
from euaiact import berechne_regel, ordne_daten_zu

F = "EUAIACT_2026_07_27"


def test_rationale_komposition_ohne_rundung_oder_mutation():
    data = {
        "arbeitsanteil_n": "2",
        "arbeitsanteil_d": "3",
        "zeit_n": "3",
        "zeit_d": "4",
    }
    before = deepcopy(data)
    mapped = ordne_daten_zu(
        data,
        {
            "mappingversion": "synthetisch-1",
            "felder": dict(
                zip(
                    [
                        "pensum_zaehler",
                        "pensum_nenner",
                        "jahresabschnitt_zaehler",
                        "jahresabschnitt_nenner",
                    ],
                    data,
                )
            ),
        },
    )
    with localcontext() as context:
        context.prec = 1
        a = berechne_regel(
            "KMU_JAE_RATIONALBEITRAG", mapped["eingaben"], quellenfassung=F
        )
        b = berechne_regel(
            "JAE_RATIONALSUMME",
            {
                "beitrag_links_zaehler": "499",
                "beitrag_links_nenner": "2",
                "beitrag_rechts_zaehler": a["wert"]["zaehler"],
                "beitrag_rechts_nenner": a["wert"]["nenner"],
            },
            quellenfassung=F,
        )
        size = berechne_regel(
            "KMU_RATIONALSCHWELLEN",
            {
                "jae_zaehler": b["wert"]["zaehler"],
                "jae_nenner": b["wert"]["nenner"],
                "jahresumsatz_eur": "0",
            },
            quellenfassung=F,
        )
    assert a["wert"] == {"zaehler": "1", "nenner": "2"}
    assert b["wert"] == {"zaehler": "250", "nenner": "1"}
    assert size["wert"] == dict(
        kleinst=False, klein=False, kmu=False, smc_groessenrahmen=True
    )
    a["wert"]["zaehler"] = "999"
    assert a["rechenschritte"][0]["wert"]["zaehler"] == "1"
    assert data == before


def test_grosse_teilerfremde_operanden():
    # Consecutive integers are coprime, including those beyond exact doubles.
    n, d = "9007199254740993", "9007199254740994"
    result = berechne_regel(
        "JAE_RATIONALSUMME",
        {
            "beitrag_links_zaehler": n,
            "beitrag_links_nenner": d,
            "beitrag_rechts_zaehler": "1",
            "beitrag_rechts_nenner": d,
        },
        quellenfassung=F,
    )
    assert result["wert"] == {"zaehler": "1", "nenner": "1"}
