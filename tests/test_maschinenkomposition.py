"""Machine-KI follow-up powers, publication and retained act validity."""

import pytest
from euaiact import berechne_regel, berechne_frist, pruefe_tatbestand

F = "EUAIACT_2026_07_27"
K = dict(von="2023-01-01", bis="2032-12-31", feiertage=[], bezug="SYNTHETISCH")


@pytest.mark.parametrize(
    "anchor,end,report,objection",
    [
        ("2023-07-19", "2028-07-19", "2027-10-19", "2028-04-19"),
        ("2026-07-27", "2031-07-27", "2030-10-27", "2031-04-27"),
    ],
)
def test_maschinenkohorten_und_vorfristen(anchor, end, report, objection):
    period = berechne_regel("OMN_003_03_DAUER_PERIODE", {}, quellenfassung=F)["wert"]
    assert (
        berechne_frist(
            anchor,
            period["anzahl"],
            period["einheit"],
            modus="FESTER_TERMIN",
            quellenfassung=F,
        )["wert"]
        == end
    )
    for rid, expected in [
        ("OMN_003_03_DAUER_BERICHT", report),
        ("OMN_003_03_DAUER_WIDERSPRUCH", objection),
    ]:
        period = berechne_regel(rid, {}, quellenfassung=F)["wert"]
        assert (
            berechne_frist(
                end,
                period["anzahl"],
                period["einheit"],
                modus="RUECKWAERTS",
                kalender=K,
                quellenfassung=F,
            )["wert"]
            == expected
        )


def test_samstagswiderruf_beendet_befugnis_erhaelt_geltenden_akt():
    timing = berechne_regel(
        "OMN_003_03_WIRKSAMKEIT",
        dict(
            widerruf_amtsblattdatum="2026-10-23",
            widerruf_spaeterer_tag_festgelegt=False,
            widerruf_prueftag="2026-10-24",
        ),
        quellenfassung=F,
    )
    assert timing["wert"] == dict(wirksam_ab="2026-10-24", am_prueftag_wirksam=True)
    rev = dict(
        maschinen_delegationsgrundlage="ART_8_3",
        akteur_ist_europaeisches_parlament=True,
        widerrufsentscheidung_tatsaechlich_erlassen=True,
        maschinen_widerruf_erfasst_betrachtete_delegation=True,
        widerrufsentscheidung_ist_zum_pruefzeitpunkt_wirksam=timing["wert"][
            "am_prueftag_wirksam"
        ],
    )
    assert (
        pruefe_tatbestand(
            "OMN_003_03_BEFUGNIS",
            rev | dict(maschinen_pruefzeitpunkt_in_wirksamer_delegationsperiode=True),
            quellenfassung=F,
        )["wert"]
        is False
    )
    assert (
        pruefe_tatbestand(
            "OMN_003_03_BESTANDSSCHUTZ",
            rev
            | dict(
                maschinenakt_beruht_auf_widerrufener_delegation=True,
                maschinenakt_vor_widerruf_bereits_in_kraft=True,
            ),
            quellenfassung=F,
        )["wert"]
        is True
    )
