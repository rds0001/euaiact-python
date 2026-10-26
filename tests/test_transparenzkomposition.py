"""Artikel 50: Zeitpunktbefund in Inhaltskriterien, Bestandsfrist separat."""

import pytest
from euaiact import (
    berechne_regel,
    pruefe_tatbestand,
    pruefe_bestandsfrist,
    ermittle_pflicht,
)

FASSUNG = "EUAIACT_2026_07_27"


@pytest.mark.parametrize(
    "information,erwartet",
    [
        ("2026-10-25T09:59:59.999999Z", True),
        ("2026-10-25T12:00:00+02:00", True),
        ("2026-10-25T10:00:00.000001Z", False),
        (None, None),
    ],
)
def test_zeitpunkt_in_kriterien_ohne_fingierte_erfuellung(information, erwartet):
    zeit = berechne_regel(
        "AIA_050_005_INFORMATIONSZEITPUNKT",
        {
            "transparenzinformation_zeitpunkt": information,
            "erste_interaktion_oder_exposition_zeitpunkt": "2026-10-25T10:00:00Z",
        },
        quellenfassung=FASSUNG,
    )
    assert zeit["wert"] is erwartet
    kriterium = pruefe_tatbestand(
        "AIA_050_005_KRITERIEN",
        {
            "transparenzinformation_klar": True,
            "transparenzinformation_unterscheidbar": True,
            "transparenzinformation_spaetestens_erste_interaktion_oder_exposition": zeit[
                "wert"
            ],
            "transparenzinformation_erfuellt_anwendbare_barrierefreiheit": True,
        },
        quellenfassung=FASSUNG,
    )
    assert kriterium["wert"] is erwartet
    assert kriterium["anwendbarkeit"] == "UNBEKANNT"
    # Sachlicher Auslöser bleibt wahr, auch bei zu später/ungeklärter Information.
    pflicht = ermittle_pflicht(
        "P_AIA_050_004_BILD",
        {
            "betreiberrolle": True,
            "ki_generiert_oder_manipuliert_bild_audio_video": True,
            "inhalt_ist_deepfake": True,
            "gesetzlich_erlaubte_straftataufdeckung_verhuetung_untersuchung_oder_verfolgung": False,
        },
        quellenfassung=FASSUNG,
    )
    assert pflicht["wert"]["ausloeser_erfuellt"] is True
    assert pflicht["wert"]["erfuellung"] == "NICHT_GEPRUEFT"


@pytest.mark.parametrize(
    "tag,friststatus",
    [
        ("2026-12-01", "VOR_FRISTTAG"),
        ("2026-12-02", "FRISTTAG"),
        ("2026-12-03", "NACH_FRISTTAG"),
    ],
)
def test_bestandsfrist_nur_fuer_kennzeichnung_synthetischer_ausgaben(tag, friststatus):
    bestand = pruefe_bestandsfrist(
        "SYNTHETISCHE_AUSGABEN_ART_50_2",
        tag,
        ereignisse={"inverkehrbringen": {"erfolgt": True, "datum": "2026-08-01"}},
        quellenfassung=FASSUNG,
    )
    assert bestand["wert"] == {
        "bestand": True,
        "erfuellungsfrist": "2026-12-02",
        "friststatus": friststatus,
    }
    assert bestand["anwendbarkeit"] == "UNBEKANNT"


def test_neues_system_am_grenztag_hat_keine_altbestandsfrist():
    bestand = pruefe_bestandsfrist(
        "SYNTHETISCHE_AUSGABEN_ART_50_2",
        "2026-12-01",
        ereignisse={"inverkehrbringen": {"erfolgt": True, "datum": "2026-08-02"}},
        quellenfassung=FASSUNG,
    )
    assert bestand["wert"]["bestand"] is False
    assert bestand["wert"]["erfuellungsfrist"] is None
