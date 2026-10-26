"""Coverage, date and reporting duties remain separate facts."""

from euaiact import berechne_regel, berechne_frist, pruefe_tatbestand, ermittle_pflicht

F = "EUAIACT_2026_07_27"


def test_gleichwertige_teilnahme_ersetzt_nicht_rechtzeitigkeit():
    coverage = pruefe_tatbestand(
        "AIA_057_001_KRITERIEN",
        {
            "nationales_ki_reallabor_betriebsbereit": False,
            "teilnahme_an_bestehendem_ki_reallabor": True,
            "teilnahme_gewaehrleistet_gleichwertige_nationale_abdeckung": True,
        },
        quellenfassung=F,
    )
    time = berechne_regel(
        "AIA_057_001_BETRIEBSTERMIN",
        {"nationale_reallaborabdeckung_betriebsbereit_seit": "2027-08-03"},
        quellenfassung=F,
    )
    duty = ermittle_pflicht(
        "P_AIA_057_001",
        {"betrachteter_akteur_ist_mitgliedstaat": True},
        quellenfassung=F,
    )
    assert coverage["wert"] is True and time["wert"] is False
    assert duty["wert"]["erfuellung"] == "NICHT_GEPRUEFT"
    assert duty["wert"]["erfuellungskriterien"] == [coverage["regel_id"]]
    assert duty["wert"]["fristregel_ids"] == [time["regel_id"]]


def test_jahres_und_schlussbericht_haben_unterschiedliche_publikationsbindung():
    annual = ermittle_pflicht(
        "P_AIA_057_016_JAHR",
        {
            "betrachteter_akteur_ist_nationale_zustaendige_behoerde": True,
            "reallabor_jahresbericht_im_betrachteten_turnus_faellig": True,
        },
        quellenfassung=F,
    )
    final = ermittle_pflicht(
        "P_AIA_057_016_SCHLUSS",
        {
            "betrachteter_akteur_ist_nationale_zustaendige_behoerde": True,
            "reallabor_tatsaechlich_beendet": True,
        },
        quellenfassung=F,
    )
    public = "AIA_057_016_JAHRESBERICHT_OEFFENTLICH"
    assert public in annual["wert"]["erfuellungskriterien"]
    assert public not in final["wert"]["erfuellungskriterien"]
    assert (
        annual["wert"]["erfuellung"] == final["wert"]["erfuellung"] == "NICHT_GEPRUEFT"
    )
    period = berechne_regel(annual["wert"]["fristregel_ids"][0], {}, quellenfassung=F)
    anniversary = berechne_frist(
        "2027-08-02",
        period["wert"]["anzahl"],
        period["wert"]["einheit"],
        modus="FESTER_TERMIN",
        quellenfassung=F,
    )
    assert anniversary["wert"] == "2028-08-02"
    # This is the explicit annual anchor; actual submission/publication stays unproved.


def test_dreimonatsparameter_und_aktgarantie_sind_keine_tatsaechliche_bewilligung():
    period = berechne_regel("AIA_058_002_A_BESCHEIDDAUER", {}, quellenfassung=F)
    end = berechne_frist(
        "2027-01-31",
        period["wert"]["anzahl"],
        period["wert"]["einheit"],
        modus="FRIST",
        kalender={
            "von": "2027-01-01",
            "bis": "2027-12-31",
            "feiertage": [],
            "bezug": "SYNTHETISCH",
        },
        quellenfassung=F,
    )
    assert end["wert"] == "2027-04-30"
    duty = ermittle_pflicht(
        "P_AIA_058_001",
        {"betrachteter_akteur_ist_europaeische_kommission": True},
        quellenfassung=F,
    )
    assert "AIA_058_002_D_AKTINHALT" in duty["wert"]["erfuellungskriterien"]
    assert duty["wert"]["erfuellung"] == "NICHT_GEPRUEFT"
    # Commission act guarantees are not an approval decision on this synthetic application.
