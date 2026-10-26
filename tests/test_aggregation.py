"""Exakte Aggregationsbausteine und Isolation vom Decimal-Kontext des Aufrufers."""

from decimal import Inexact, Rounded, localcontext
from euaiact import berechne_regel

FASSUNG = "EUAIACT_2026_07_27"


def test_ganzer_uebertrag_an_eingabegrenze():
    e = berechne_regel(
        "KMU_VERBUND_HINZURECHNUNG",
        {
            "aggregationsbasiswert": "9" * 4096,
            "noch_hinzuzurechnender_unternehmenswert": "1",
        },
        quellenfassung=FASSUNG,
    )
    assert e["status"] == "AUSGEWERTET"
    assert e["wert"] == "1" + "0" * 4096
    # Keine heimliche Kürzung auf das Eingabelimit: Weiterverwendung validiert erneut.
    erneut = berechne_regel(
        "KMU_VERBUND_HINZURECHNUNG",
        {
            "aggregationsbasiswert": e["wert"],
            "noch_hinzuzurechnender_unternehmenswert": "0",
        },
        quellenfassung=FASSUNG,
    )
    assert erneut["status"] == "EINGABE_UNGUELTIG"


def test_bruchstellen_und_ergebnis_unter_einem_cent_bleiben_erhalten():
    e = berechne_regel(
        "KMU_PARTNER_HINZURECHNUNG",
        {
            "aggregationsbasiswert": "0.00000000000000000001",
            "noch_hinzuzurechnender_unternehmenswert": "0.00000000000000000002",
            "hinzurechnungsquote": "0.25",
        },
        quellenfassung=FASSUNG,
    )
    assert e["wert"] == "0.000000000000000000015"
    assert e["rechenschritte"][0]["wert"] == "0.000000000000000000005"


def test_fremder_decimal_kontext_aendert_keine_rechnung():
    with localcontext() as kontext:
        kontext.prec = 2
        kontext.Emax = 3
        kontext.Emin = -3
        kontext.traps[Inexact] = True
        kontext.traps[Rounded] = True
        e = berechne_regel(
            "KMU_PARTNER_HINZURECHNUNG",
            {
                "aggregationsbasiswert": "0.75",
                "noch_hinzuzurechnender_unternehmenswert": "9007199254740993",
                "hinzurechnungsquote": "0.25",
            },
            quellenfassung=FASSUNG,
        )
        assert e["wert"] == "2251799813685249"
        busse = berechne_regel(
            "AIA_101_OBERGRENZE",
            {"weltweiter_vorjahresumsatz_eur": "1000000000"},
            quellenfassung=FASSUNG,
        )
        assert busse["wert"] == "30000000"
        assert kontext.prec == 2 and kontext.Emax == 3
        assert not any(kontext.flags.values())


def test_maximale_multiplikationslaengen_ohne_rundung():
    # (10^4096-1)*(1-10^-4094) = 10^4096-101+10^-4094.
    e = berechne_regel(
        "KMU_PARTNER_HINZURECHNUNG",
        {
            "aggregationsbasiswert": "0",
            "noch_hinzuzurechnender_unternehmenswert": "9" * 4096,
            "hinzurechnungsquote": "0." + "9" * 4094,
        },
        quellenfassung=FASSUNG,
    )
    assert e["status"] == "AUSGEWERTET"
    assert e["wert"] == "9" * 4093 + "899." + "0" * 4093 + "1"
