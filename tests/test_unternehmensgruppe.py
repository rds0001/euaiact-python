"""Independent graph/consolidation/identity and exact arithmetic references."""

import json
from pathlib import Path
from copy import deepcopy
import pytest
from jsonschema import validate
from euaiact import aggregiere_unternehmensgruppe, schema_info

CASES = json.loads(
    (Path(__file__).parent / "fixtures/unternehmensgruppe_referenzen.json").read_text()
)["faelle"]


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["fall_id"])
def test_unternehmensgruppe(case):
    data = deepcopy(case["eingaben"])
    result = aggregiere_unternehmensgruppe(**data)
    assert data == case["eingaben"]
    assert result["status"] == case["erwartung"]["status"], result
    assert result["wert"] == case["erwartung"]["wert"], case["herleitung"]
    validate(result, schema_info("ERGEBNIS_0_1_0"))


def test_reihenfolge_aendert_keine_ergebnisspur():
    a = aggregiere_unternehmensgruppe(**CASES[0]["eingaben"])
    b = aggregiere_unternehmensgruppe(**CASES[3]["eingaben"])
    for key in a:
        if key != "eingaben":
            assert a[key] == b[key]


def test_ergebnis_mutiert_keine_fremden_unternehmensdaten():
    data = deepcopy(CASES[0]["eingaben"])
    result = aggregiere_unternehmensgruppe(**data)
    result["eingaben"]["datenkreise"][0]["wert"] = "999"
    assert data == CASES[0]["eingaben"]


def test_beziehungswechsel_wird_nicht_als_regulaere_statusfortschreibung_behandelt():
    from euaiact import berechne_regel, pruefe_tatbestand

    f = "EUAIACT_2026_07_27"
    data = dict(
        stamm_id="A",
        unternehmen=["A", "B"],
        beziehungen=[dict(von="A", nach="B", art="PARTNER", quote="0.25")],
        datenkreise=[
            dict(
                kreis_id=id,
                unternehmen_ids=[id],
                wert=dict(zaehler=str(n), nenner="1"),
                personensegmente=[
                    dict(person_id=id + str(i), segment_id="Jahr") for i in range(n)
                ],
            )
            for id, n in [("A", 6), ("B", 8)]
        ],
        groesse="JAE",
        bezugsperiode="2025",
        kreis_vollstaendig=True,
        quellenfassung=f,
    )
    before = aggregiere_unternehmensgruppe(**data)["wert"]["summe"]
    data["beziehungen"] = [dict(von="A", nach="B", art="VERBUND")]
    after = aggregiere_unternehmensgruppe(**data)["wert"]["summe"]
    assert before == dict(zaehler="8", nenner="1") and after == dict(
        zaehler="14", nenner="1"
    )

    def size(v):
        return berechne_regel(
            "KMU_RATIONALSCHWELLEN",
            dict(
                jae_zaehler=v["zaehler"],
                jae_nenner=v["nenner"],
                jahresumsatz_eur="100",
                jahresbilanzsumme_eur="100",
            ),
            quellenfassung=f,
        )["wert"]["kleinst"]

    old, current = size(before), size(after)
    assert old is True and current is False
    state = dict(
        regulaere_groessenfortschreibung_ohne_strukturwechsel_oder_neugruendung=False,
        groessenrahmen_in_aktueller_abschlussperiode_erfuellt=current,
        groessenrahmen_in_unmittelbarer_vorperiode_erfuellt=old,
        groessenrahmenstatus_vor_aktueller_periodenpruefung=True,
    )
    assert (
        pruefe_tatbestand("KMU_ZWEIPERIODEN_GROESSENRAHMEN", state, quellenfassung=f)[
            "status"
        ]
        == "REGEL_UNGEKLAERT"
    )
    # Separate hypothetical ordinary headcount change, expressly no transaction.
    state["regulaere_groessenfortschreibung_ohne_strukturwechsel_oder_neugruendung"] = (
        True
    )
    assert (
        pruefe_tatbestand("KMU_ZWEIPERIODEN_GROESSENRAHMEN", state, quellenfassung=f)[
            "wert"
        ]
        is True
    )
    state["groessenrahmen_in_unmittelbarer_vorperiode_erfuellt"] = False
    assert (
        pruefe_tatbestand("KMU_ZWEIPERIODEN_GROESSENRAHMEN", state, quellenfassung=f)[
            "wert"
        ]
        is False
    )
