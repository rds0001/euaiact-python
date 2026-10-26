# Kern-API

`schema_info(schema_id="ERGEBNIS_0_1_0")` liefert das mitgelieferte JSON-Schema
des Ergebnisumschlags als unabhängiges Dictionary. Unbekannte IDs lösen `KeyError`
aus. Schema-URIs sind Metadaten; die Library ruft sie nicht auf. Eine externe
Schema-Prüfung kann ebenfalls vollständig lokal erfolgen. Regeln mit noch
unbekannten Tatsachen und ungültigen Eingaben behalten dieselben Umschlagsfelder.

`regel_katalog()` liefert IDs, Beschreibungen, Quellenfassung und Bearbeitungsstatus.
`regel_info(regel_id)` liefert eine unabhängige Kopie der vollständigen Spezifikation
und löst für unbekannte IDs `KeyError` aus.

`eingabevertrag(regel_id)` liefert alle Feldverträge einschließlich transitiver
Regelverweise, sortiert nach Feldname. Das Ergebnis enthält Regel-, Quellen- und
Schemaversion, `felder`, `unbekannt` und `zusaetzliche_felder`. Es ist unabhängig
veränderbar. Gerade zusammengesetzte Regeln benötigen mehr Felder als die eigenen
unmittelbaren `eingaben` in `regel_info`; dieser Vertrag erschließt die vollständige
Schnittstelle. Für Zeit- und Fristfunktionen gelten ihre separat dokumentierten
Parameterverträge.

`pruefe_tatbestand(regel_id, eingaben, *, quellenfassung)` prüft Fakten aus einem
Dictionary. Booleanfelder akzeptieren ausschließlich `True`, `False` und `None`.
Dezimalfelder erwarten Zeichenfolgen wie `"123.45"`, maximal 4096 Zeichen,
ohne Exponent, Tausendertrennzeichen oder Komma. Fehlende Felder und `None`
bedeuten unbekannt. Unbekannte Schlüssel und falsche Typen sind ungültig.

Der Ergebnisumschlag enthält den Wert, technische und fachliche Statusangaben,
Regel-/Quellen-/Schemaversion, Eingaben, Entscheidungsschritte, Annahmen, Hinweise,
fehlende Angaben, entscheidungsrelevante Lücken und Quellenverweise. Ein falscher
Wert wird als `False` zurückgegeben, ein unbekannter Wert als `None`.

`AUSGEWERTET` bedeutet, dass der sachliche Tatbestand entschieden werden konnte.
`EINGABE_FEHLT` bezeichnet entscheidungsrelevante unbekannte Angaben.
`EINGABE_UNGUELTIG` bezeichnet einen nicht verwertbaren Eingabesatz; der Wert bleibt
leer. Die allgemeine rechtliche Anwendbarkeit wird in dieser Funktion nicht
bestimmt. Sie bleibt bei gültigen Eingaben `UNBEKANNT`, auch bei entschiedenem Wert.

`pruefe_stapel(faelle, *, quellenfassung)` erhält eine Liste von Dictionaries mit
genau `fall_id`, `regel_id` und `eingaben`. Doppelte/leere IDs oder ungültige
Stapelstruktur lösen `ValueError` aus. Fehlerhafte Fakten bleiben je Fall isoliert.

Keine Funktion verändert übergebene Daten oder startet Netzwerkzugriffe. Ein
Katalogeintrag mit dokumentierter Implementierung ist keine allgemeine rechtliche
Freigabe. Bearbeitungsstatus und verbleibende Grenzen werden im Ergebnis ausgewiesen.

`berechne_regel(regel_id, eingaben, *, quellenfassung)` wertet die Rechenregeln
des Katalogs aus. `berechne_bussgeldobergrenze(eingaben, *, quellenfassung)` ist
der fachliche Einstieg für Artikel 99. Hier sind `verstosskategorie`
(`VERBOT`, `PFLICHT`, `INFORMATION`), `akteurklasse` (`KEIN_UNTERNEHMEN`, `KMU`,
`SMC`, `SONSTIGES_UNTERNEHMEN`) und bei Unternehmen
`weltweiter_vorjahresumsatz_eur` anzugeben.

Geldbeträge werden exakt als Dezimalzeichenfolgen ausgegeben, ohne implizite
Cent-Rundung. Berechnet wird eine gesetzliche Obergrenze, kein tatsächliches
Bußgeld. `KMU_SCHWELLEN` liefert Größenmerkmale; Beteiligungen, Aggregation und
Statushistorie sind zusätzlich erforderlich, um den Größenstatus zu bestimmen.

`berechne_frist(ereignisdatum, anzahl, einheit, *, modus, kalender,
quellenfassung)` verwendet ISO-Datumszeichenfolgen (Jahre 0001–9999), eine positive
ganze Zahl und `TAG`, `ARBEITSTAG`, `WOCHE`, `MONAT` oder `JAHR`. Der Kalender
enthält genau `von`, `bis`, `feiertage` (Liste eindeutiger ISO-Daten innerhalb
der Deckung) und `bezug` (nichtleerer Herkunftstext). Modus `FRIST` berücksichtigt
arbeitsfreie Endtage und die Mindestzahl von zwei Arbeitstagen ab Zweitagesfristen.
`FESTER_TERMIN` und `INKRAFTTRETEN` wenden diese Verlängerungen nicht an.
Bei diesen beiden Modi kann `kalender` entfallen, sofern die Einheit nicht
`ARBEITSTAG` ist. Gelieferte Kalender werden dennoch validiert.
Monate/Jahre verwenden den entsprechenden Tag oder letzten Zielmonatstag.
Fehlende Kalenderdeckung ergibt `EINGABE_FEHLT`, ungültige Angaben
`EINGABE_UNGUELTIG`. Zusätzlich nimmt `STUNDE` mit `modus="FRIST"` im Parameter
`ereignisdatum` einen ISO-Zeitstempel mit explizitem UTC-Offset entgegen.
Die Ereignisstunde wird ausgeschlossen; `wert` enthält `beginn` und
`ende_exklusiv` als UTC-Texte. Kein automatisches Verschieben auf Werktage.
Ab48Stunden bleibt F011 mit `REGEL_UNGEKLAERT` ohne Fachwert sichtbar.
Dieser allgemeine Stundenvertrag bestimmt keine speziellen AI-Act-Höchstgrenzen.
Eine Pflicht zu unverzüglichem Handeln bleibt separat.

```python
from euaiact import berechne_frist
ergebnis = berechne_frist("2026-10-23", 2, "TAG", modus="FRIST",
    kalender={"von": "2026-01-01", "bis": "2026-12-31", "feiertage": [],
              "bezug": "SYNTHETISCH: keine Feiertage"},
    quellenfassung="EUAIACT_2026_07_27")
assert ergebnis["wert"] == "2026-10-27"
```

`lese_json(pfad)` und `schreibe_json(daten, pfad)` bieten lokalen UTF-8-Austausch
(maximal 16 MiB, 100 Verschachtelungsebenen). URLs/URIs und UNC-Pfade werden
abgelehnt. Verwenden Sie lokale Datenträger; vom Betreiber eingebundene
Dateisysteme werden nicht automatisch erkannt. Unterstützt werden Dictionaries
mit eindeutigen nichtleeren Textschlüsseln, Listen, Text, Boolean, `None` und
ganze Zahlen bis absolut 9007199254740991. Dezimalwerte sind Text. Der Export
überschreibt niemals vorhandene Dateien. Vertragsfehler lösen `ValueError`,
Betriebssystemfehler `OSError` bzw. Unterklassen aus. Ein fehlgeschlagener
Schreibvorgang kann eine unvollständige neue Datei hinterlassen.

`ordne_daten_zu(datensatz, zuordnung)` arbeitet rein im Speicher. Die Zuordnung
enthält genau `mappingversion` und `felder` (Zielfeld auf direkten Quellfeldnamen).
Zielnamen entsprechen `[a-z][a-z0-9_]*`. Keine Pfadausdrücke oder Transformationen.
Das Ergebnis enthält `mappingversion`, `eingaben` und `herkunft`, sortiert nach
Zielfeld. Herkunftseinträge enthalten `zielfeld`, `quellfeld`, `vorhanden`.
Fehlende Quellfelder ergeben `None`; vorhandenes `None` bleibt in der Herkunft
unterscheidbar. Nicht ausgewählte Daten werden nicht übernommen. Der Fachkern
prüft anschließend Typ und Wertebereich der konkreten Regel.

```python
from euaiact import ordne_daten_zu
daten = ordne_daten_zu({"heilzweck": False}, {
    "mappingversion": "beispiel-1",
    "felder": {"medizinisch": "heilzweck", "arbeitsplatz": "betrieb"}})
assert daten["eingaben"] == {"arbeitsplatz": None, "medizinisch": False}
```

`pruefe_anwendungsbeginn(bereich, stichtag, *, quellenfassung)` vergleicht ein
ISO-Datum mit dem allgemeinen Beginn nach Artikel 113. Quellenfassungen:
`EUAIACT_2024_08_01` und `EUAIACT_2026_07_27`. Stichtage vor Inkrafttreten der
gewählten Fassung sind ungültig; fehlende Werte bleiben unbekannt. Ein älterer
Stand kann ausdrücklich eine damalige Planung für spätere Daten abbilden.
Artikel 111 und die übrigen Geltungsbereichsvoraussetzungen bleiben separat.
Das Vergleichsdatum steht in `entscheidungsschritte`; `anwendbarkeit` bleibt
`UNBEKANNT`. Keine automatische Auswahl eines Bereichs oder einer Fassung.

Zulässige Bereiche in beiden Fassungen: `ALLGEMEIN`, `KAPITEL_I_II_BESTAND`,
`KAPITEL_III_ABSCHNITT_4`, `KAPITEL_V`, `KAPITEL_VII`,
`KAPITEL_XII_OHNE_101`, `ARTIKEL_78`, `ARTIKEL_101`, `ARTIKEL_6_5`,
`ARTIKEL_102_BIS_110`, `HOCHRISIKO_ANHANG_III_ABSCHNITT_1_BIS_3_OHNE_6_5`.
Nur 2024: `HOCHRISIKO_ANHANG_I_ARTIKEL_6_1_UND_ZUGEHOERIGE_PFLICHTEN`.
Nur 2026: `HOCHRISIKO_ANHANG_I_ABSCHNITT_1_BIS_3_OHNE_6_5`,
`ARTIKEL_5_BA_BB_1A_1B`. Der Kapitel-I/II-Bestand schließt Artikel 4a und die
neuen Verbote aus. Für Artikel 4a besteht noch eine dokumentierte Auslegungsfrage.

```python
from euaiact import pruefe_anwendungsbeginn
assert pruefe_anwendungsbeginn("ARTIKEL_5_BA_BB_1A_1B", "2026-12-01",
    quellenfassung="EUAIACT_2026_07_27")["wert"] is False
```

## Bestandsfristen

`pruefe_bestandsfrist(fallgruppe, stichtag, *, ereignisse, quellenfassung)`
prüft Artikel 111. Die bisherigen Fallgruppen für Absätze 1, 3 und 4 sind:
`GROSS_IT_ANHANG_X`, `GPAI_MODELL`, `SYNTHETISCHE_AUSGABEN_ART_50_2`.
Die Fallqualifikation ist Voraussetzung und wird ausdrücklich vom Aufrufer
vorgenommen. Die Hochrisiko-Fallgruppen für Absatz 2 sind unten beschrieben;
die Gesamtgeltung bleibt separat zu prüfen.

```python
from euaiact import pruefe_bestandsfrist

pruefe_bestandsfrist(
    "GPAI_MODELL", "2027-08-02",
    ereignisse={"inverkehrbringen": {"erfolgt": True, "datum": "2025-08-01"}},
    quellenfassung="EUAIACT_2026_07_27",
)["wert"]
# {"bestand": True, "erfuellungsfrist": "2027-08-02", "friststatus": "FRISTTAG"}
```

Für diese drei Fallgruppen erlaubt `ereignisse` `inverkehrbringen` und
`inbetriebnahme`; ein Ereignis ist
`None` oder ein Objekt mit `erfolgt` (bool/None) und `datum` (ISO-Datum/None).
Ein bekanntes Datum verlangt `erfolgt=True` und darf nicht nach dem Stichtag
liegen. Alle gelieferten Ereignisse werden validiert. Bei Groß-IT genügt eine
bekannte alte Einführung oder Inbetriebnahme, auch wenn die andere unbekannt ist.
Die Bestandsgrenzen sind strikt vor 2027-08-02 (Groß-IT), 2025-08-02 (GPAI) und
2026-08-02 (synthetische Ausgaben); Fristen: 2030-12-31, 2027-08-02, 2026-12-02.
Die synthetische Fallgruppe ist nur in der Quellenfassung 2026 verfügbar.

Das Ergebnisobjekt enthält `bestand`, `erfuellungsfrist` und `friststatus`:
`VOR_FRISTTAG`, `FRISTTAG`, `NACH_FRISTTAG`, `KEINE_BESTANDSFRIST` oder
`UNBESTIMMT`. Fehlende Ereignisdaten bleiben unbekannt; feste gesetzliche Termine
werden nicht wegen Wochenenden verschoben. Ein überschrittener Termin besagt
nichts darüber, ob die Pflichten tatsächlich erfüllt wurden. Artikel 5 bleibt
unberührt. Artikel 50 Absatz 2 wird nicht auf andere Transparenzpflichten erweitert.

Der zusätzliche Fristmodus `VERFAHREN_1755_TAGE` gilt ausschließlich für
Tagesfristen im einschlägigen GPAI-Kommissionsverfahren nach Artikel 12 Absatz 2
DVO 2026/1755. Der erste folgende Arbeitstag ist Tag 1; anschließend gelten die
normalen Endregeln. Nur `TAG` und `ARBEITSTAG` sind hier zulässig. Bei einem
Freitagsereignis und drei Kalendertagen ohne Feiertage endet diese Frist am
Mittwoch. Die allgemeine `FRIST` wird durch diesen Sondermodus nicht verändert.

Logikauswertungen führen in `nachweise` auch die Fundstellen der durchlaufenen
Unterregeln auf, jeweils mit `regel_id` und `regelversion`. Ihre fachlichen
Grenzen stehen zusätzlich mit Regel-ID in `hinweise`. Die Reihenfolge folgt dem
ersten Besuch; mehrfach referenzierte Regeln erhalten nur eine Beleggruppe.
Die Liste enthält auch betrachtete, logisch nicht entscheidende Zweige.

`berechne_regel("AIA_073_MELDEFRISTTAGE", eingaben, quellenfassung=...)`
liefert die äußerste Tagesdauer einer bereits qualifizierten Vorfallmeldung:
2 Tage bei `weitverbreiteter_verstoss=True` oder
`schwere_irreversible_kritische_infrastrukturstoerung=True`; sonst 10 bei
`todesfall=True`, ansonsten 15. Alle Felder sind bool/None. Ein bekannter
Zweitagesgrund entscheidet trotz weiterer Datenlücken; sonst bleiben fehlende
entscheidende Fakten unbekannt. Gelieferte falsche Typen werden immer abgewiesen.

Diese Höchstdauer ersetzt keine unverzügliche Meldung. Meldepflicht, Kenntnistag,
Vorfallschwere und Einschränkungen des Artikels 73 Absätze 9/10 separat prüfen;
das Kalenderdatum kann anschließend mit `berechne_frist` berechnet werden.

Die Regeln `AIA_002_002_NORMGRUPPE_ZULAESSIG` und
`AIA_002_013_VORAUSSETZUNGEN` ergänzen die normbezogene Bereichsprüfung.
Ihre ENUM-Kategorien stehen in `eingabevertrag(regel_id)`. Ein positives
Ergebnis der ersten Regel besagt ausschließlich, dass Artikel 2 Absatz 2 die
Normgruppe nicht ausschließt. Die zweite Regel prüft Voraussetzungen einer
möglichen Begrenzung; sie bestätigt keinen bereits erlassenen delegierten
Ausnahmeakt. Artikel 16 ist nicht in den begrenzbaren Gruppen 9–15/17–25.

## Strukturierte Pflichtauslösung

`pflicht_katalog()` liefert unabhängige Kopien des verfügbaren Teilkatalogs mit
Pflicht-ID/-Version, Auslöserregel, Adressat, Rechtsfolge, Ausnahmen, Zeitbezug,
Nachweisarten, Kriterien und Bearbeitungsstatus.

```python
from euaiact import ermittle_pflicht

ergebnis = ermittle_pflicht(
    "P_AIA_026_007",
    {"betreiberrolle": True, "hochrisikosystem": True,
     "betreiber_ist_arbeitgeber": True, "einsatz_am_arbeitsplatz_geplant": True},
    quellenfassung="EUAIACT_2026_07_27",
)
assert ergebnis["wert"]["ausloeser_erfuellt"] is True
assert ergebnis["wert"]["erfuellung"] == "NICHT_GEPRUEFT"
```

`ermittle_pflicht(pflicht_id, eingaben, *, quellenfassung)` verwendet die im
Katalog hinterlegte Auslöserregel. Den Feldvertrag liefert
`eingabevertrag(ausloeser_regel)`. Der volle Ergebnisumschlag enthält weiterhin
Entscheidungsspur und Quellen; `wert` wird ein Objekt mit Pflicht-ID/-Version,
`ausloeser_erfuellt`, Adressat, Rechtsfolge, Zeitbezug, Nachweisarten,
Erfüllungskriterien und `erfuellung="NICHT_GEPRUEFT"`.

Die Rechtsfolge beschreibt immer die bedingte Pflicht, auch bei falschem oder
unbekanntem Auslöser. Anwendbarkeit bleibt `UNBEKANNT`; Erfüllung und Belege sind
separat zu prüfen. Unbekannte IDs oder ungültige Fakten liefern
`EINGABE_UNGUELTIG` mit `wert=None`; entscheidende Datenlücken liefern
`EINGABE_FEHLT` mit partiellem Objekt. Es wird keine externe Aktion ausgeführt.

`schema_info("<regel_id>:EINGABEN")` liefert lokale Eingabeschemata für alle
Katalogregeln. Felder sind optional und erlauben null. Exakte Dezimalgrenzen
sind Annotationen; ihre Prüfung erfolgt in der nativen Regelauswertung.

Für `pruefe_anwendungsbeginn("ARTIKEL_4A", ...)` in der Fassung 2026 ist
die offene Rechtsfrage F002 explizit abgebildet: vollständige gültige Eingaben
liefern `REGEL_UNGEKLAERT`, keine geschätzte zeitliche Anwendbarkeit.

`berechne_regel("AIA_030_EINWANDSPERIODE", ...)` wählt bei Notifizierung mit
Akkreditierungsbescheinigung zwei Wochen, bei Dokumentennachweisen zwei Monate.
Der Objektwert enthält `anzahl` und `einheit` zur Übergabe an `berechne_frist`.
Einwände und tatsächlichen Fristablauf gesondert prüfen; keine automatische
Berechtigung zur Tätigkeit als benannte Stelle.

## Lokale Anhangtabellen

`tabellen_katalog()` listet fünf versionierte Tabellen. `tabelle_info(tabellen_id)`
liefert Spalten, Zeilen, Quellenfassung, Texthash, Status und Grenzen als unabhängige
Kopie. IDs: `ANH_I`, `ANH_II`, `ANH_X`, `ANH_XIII`, `ANH_XIV`. Unbekannte oder
nicht textuelle ID: `KeyError`. Kein Netzwerk, keine implizite Rechtsaktaktualisierung.

```python
from euaiact import tabelle_info
produkte = tabelle_info("ANH_I")
maschinen = [z for z in produkte["zeilen"] if z["celex"] == "32023R1230"]
assert maschinen[0]["abschnitt"] == "B"
```

77 Zeilen decken die fünf Listen ab; konkrete Produktanwendbarkeit, Straftatzuordnung,
GPAI-Benennung und Notifizierung bleiben eigene Prüfungen. Eigene Daten können
explizit über CELEX, amtliche Codes oder `eintrag_id` verbunden werden.

Die Rechenregeln `KMU_PARTNER_HINZURECHNUNG` und
`KMU_VERBUND_HINZURECHNUNG` verwenden `berechne_regel`. Eingaben sind exakte,
nichtnegative Dezimaltexte `aggregationsbasiswert` und
`noch_hinzuzurechnender_unternehmenswert`; beim Partner zusätzlich
`hinzurechnungsquote` zwischen `"0"` und `"1"`. Ergebnis: Basis plus gewichteter
Zusatzwert, beim Verbund mit fester Quote 1, ohne Rundung. Beide Werte müssen
dieselbe Kennzahl, Einheit und Periode betreffen. Bereits konsolidierte Werte
sind vorab auszuschließen; die Funktion ermittelt keinen Beteiligungsgraphen und
keinen abschließenden Größenstatus. Rechenschritte zeigen Multiplikation und
Addition. Auch bei Weiterverwendung eines Ergebnisses gilt das Eingabelimit
von 4096 Zeichen je Dezimalwert.

Bei einer entscheidungsrelevanten offenen Rechtsauslegung kann
`pruefe_tatbestand` den Status `REGEL_UNGEKLAERT` liefern. Das ist keine fehlende
Unternehmensangabe: Die betreffende Frage steht als `frage_id` bzw.
`offene_rechtsfragen` in der Entscheidungsspur und in den Hinweisen. Gleichzeitig
fehlende Tatsachen bleiben separat in den Datenlücken. Rechtsfragen lassen sich
nicht durch zusätzliche Nutzereingaben überschreiben. Ein bestimmendes anderes
UND-/ODER-Glied kann die offene Frage unerheblich machen.

Konkrete Beispiele sind die unterschiedlichen deutschen/englischen
Business-Angel-Grenzwortlaute: exakt 5 Millionen EUR bei SMC (F015) und exakt
1,25 Millionen EUR bei KMU (F016). Ein ausschließlich darauf beruhender
Investorenausnahmefall bleibt offen; Werte darunter/darüber und unabhängige
andere Tatbestände werden weiterhin bestimmt ausgewertet.


Zeitpunkte für Transparenzinformationen lassen sich mit
`berechne_regel("AIA_050_005_INFORMATIONSZEITPUNKT", ...)` vergleichen. Die Felder
`transparenzinformation_zeitpunkt` und
`erste_interaktion_oder_exposition_zeitpunkt` enthalten ausdrücklich qualifizierte
Ereignisse derselben Person und desselben System-/Inhaltskontexts. Beispiel:
`2026-10-25T12:00:00+02:00` entspricht `2026-10-25T10:00:00Z`.
Gleichzeitigkeit genügt; schon eine Mikrosekunde Verspätung ergibt `False`/`FALSE`.
Das technische Profil verlangt Jahre 0001–9999, `T`, vollständige Sekunden und
`Z` oder einen expliziten Offset `±HH:MM`; optional sind ein bis sechs
Nachkommastellen erlaubt. Schaltsekunden, `-00:00` (unbekannter Offset),
Uhrzeiten ohne Offset und implizite Datumsobjekt-Konvertierungen werden abgewiesen.
Die Library verwendet weder die Rechnerzeitzone noch die aktuelle Uhrzeit.
Geprüft wird nur die Zeitrelation, nicht die Informationsqualität oder die
Anwendbarkeit der Pflicht. Die übrigen Artikel-50-Kriterien bleiben separat.


`ermittle_pflicht` gibt neben Auslöser und Rechtsfolge auch `gegenstand`,
`ausnahmen`, `fundstellen` und `fristregel_ids` aus. Die Frist-/Zeitregel-IDs
sind mit `regel_info` und `berechne_regel` direkt nutzbar. Beispielsweise verweist
`P_AIA_050_001` auf `AIA_050_005_INFORMATIONSZEITPUNKT`, die GPAI-Meldepflicht
auf ihren gesetzlichen Höchstdauerparameter. Ein Verweis führt die Prüfung
nicht automatisch aus: Die eigenen Ereignisdaten sind ausdrücklich zu übergeben.
`erfuellung` bleibt bei diesem Auslöseraufruf `NICHT_GEPRUEFT`.


`berechne_frist(..., modus="RUECKWAERTS")` rechnet positive ganze Perioden
vor dem angegebenen Bezugstag zurück, der selbst nicht mitzählt. Einheiten:
TAG, ARBEITSTAG, WOCHE, MONAT, JAHR. Expliziter Kalender erforderlich.
Ein Wochenende am Grenztag wird nicht verschoben. Bei Perioden ab zwei Tagen
bleiben mindestens zwei Arbeitstage notwendig; hierfür wird gegebenenfalls
weiter zurückgerechnet. Monats-/Jahreskorrespondenz mit letztem Monatstag als
Ersatz bei fehlendem Tag. Ergebnis bezeichnet den Ablauf des Grenztags.
Die Funktion entscheidet nicht selbst über den passenden juristischen Modus.


`berechne_regel("AIA_027_001_VOR_EINSATZ", eingaben, quellenfassung=...)`
vergleicht `fria_abschluss_zeitpunkt` strikt mit `erstmaliger_einsatz_zeitpunkt`.
Beide sind DATUMZEIT-Texte nach obigem Profil. Gleiche UTC-Instanten ergeben
False; ein abweichender Offset oder eine anders ausgeschriebene Nachkommastelle
macht sie nicht verschieden. Die Pflichtausgabe für `P_AIA_027_002_ERSTE`
verweist auf diese Regel. Sachliche Pflicht und sechs FRIA-Inhalte separat prüfen.


Jahresarbeitseinheiten: `KMU_PERSONALKREIS`/`SMC_PERSONALKREIS` und die Regeln
`KMU_JAE_ZEITABSCHNITT`/`SMC_JAE_ZEITABSCHNITT` prüfen Person und homogenen
Zeitabschnitt. `KMU_JAE_DEZIMALBEITRAG`/`SMC_JAE_DEZIMALBEITRAG` multiplizieren
`arbeitszeitanteil_an_vollzeit` und `anrechenbarer_jahresanteil`, beide exakt
endliche Dezimaltexte von 0 bis 1. `JAE_DEZIMALSUMME` addiert
`bisherige_jahresarbeitseinheiten` und `zusaetzliche_jahresarbeitseinheiten`.
Keine automatische Zeitbasis, Segmentdeduplizierung oder Rundung periodischer
Brüche wie 1/3; allgemeine rationale Quotenermittlung ist nicht enthalten.


`KMU_ZWEIPERIODEN_GROESSENRAHMEN` und `SMC_ZWEIPERIODEN_GROESSENRAHMEN`
prüfen die reguläre Fortschreibung anhand bisherigen wirksamen Rahmenstatus
und der Schwellenbefunde zweier unmittelbar aufeinanderfolgender Perioden.
Übereinstimmende Perioden bestimmen den Rahmen, andernfalls bleibt der bisherige
Status. Sonderanlässe sind ausdrücklich von der regulären Kontextangabe
abgegrenzt und ergeben entscheidungsrelevant F008. SMC-Obergrößenrahmen ist
kein vollständiger SMC-Status. Neugründungsschätzung wird über die separaten
`KMU_NEUGRUENDUNG_DATENGRUNDLAGE`/`SMC_NEUGRUENDUNG_DATENGRUNDLAGE` geprüft.


Die Eingabeverträge sämtlicher Katalogregeln enthalten jetzt eine fachliche
`definition`, die erwartete `herkunft` und den maßgeblichen `bezugszeit`-Kontext.
`schema_info(regel_id + ":EINGABEN")` stellt diese Angaben auch im lokalen
JSON-Schema bereit. Boolesche Nachweisfelder speichern weder das Originaldokument
noch echte Unternehmensstammdaten: Sie setzen eine begründete Bewertung des
konkreten Vorgangs voraus. Bewahren Sie die zugrunde liegenden Belege und die
Bewertungsbegründung in Ihrer eigenen lokalen Datenhaltung auf und verbinden Sie
sie über stabile Vorgangskennungen mit den Eingaben und Ergebnissen. Ungeklärte
Sachverhalte bleiben unbekannt; offene Rechtsfragen werden dadurch nicht aufgelöst.

## Hochrisiko-Bestand und Entwurfsänderungen

Dieselbe API unterstützt `HOCHRISIKO_ANHANG_I`, `HOCHRISIKO_ANHANG_III` und
`HOCHRISIKO_DOPPELT` für Artikel 111 Absatz 2. Die Fallqualifikation schließt
den Groß-IT-Sonderfall des Absatzes 1 aus. Erhebliche Entwurfsänderungen und
die Frist für Anbieter/Betreiber behördlich bestimmter Systeme sind getrennte
Ergebnisfelder. Vollständiger Eingabe-/Ergebnisvertrag mit Datenherkunft:
[Übergangsvertrag](UEBERGANG.md).

```python
ergebnis = pruefe_bestandsfrist(
    "HOCHRISIKO_ANHANG_III", "2030-08-02",
    ereignisse={
        "inverkehrbringen": {"erfolgt": True, "datum": "2027-12-01"},
        "inbetriebnahme": {"erfolgt": False},
        "aenderungen": [],
        "aenderungshistorie_vollstaendig": True,
        "fuer_behoerden_bestimmt": True,
        "anbieter_oder_betreiber": True,
    },
    quellenfassung="EUAIACT_2026_07_27",
)
# bestand=True; aenderungsvorbehalt_ausgeloest=False;
# behoerdenfrist_betroffen=True; erfuellungsfrist="2030-08-02"; friststatus="FRISTTAG"
```

Eine leere Änderungsliste ohne bestätigte Vollständigkeit bleibt unbekannt.
Die Doppelklassifikation prüft beide Stichtage: gleiche Ergebnisse bleiben
nutzbar, abweichende Felder führen zu `REGEL_UNGEKLAERT` (F004).

## Wissenschaftliches Gremium: Transparenz

`DVO_0454_012_BASISINHALTE` prüft öffentliche Namen, Lebensläufe, drei
Erklärungsarten und Geschäftsordnung. `DVO_0454_012_PUBLIKATIONSWEG` prüft
den vorgeschriebenen Veröffentlichungsort und die qualifizierte Bereitstellung
ohne unangemessene Verzögerung. Für Stellungnahmen/Empfehlungen ist
`DVO_0454_012_STELLUNGNAHMEPFLICHT` der gesonderte Auslöser: jeder der
drei gesetzlich benannten Schutzgründe kann diesen Veröffentlichungspunkt
ausnehmen. Das beseitigt die Grundinformationspflicht nicht.

Die zwei zugehörigen Pflichtdatensätze geben Erfüllungskriterien an; ein
ausgelöster Tatbestand bedeutet keine bereits erfolgte Veröffentlichung.
Alle Publikations- und Schutzangaben werden aus eigenen lokalen Nachweisen
übergeben, ohne Netzwerkzugriff. Der unzutreffende Anhörungsverweis in Artikel12
bleibt als F017 getrennt offen; die tatsächliche Veröffentlichung nach Artikel7(5)
bleibt über den bestehenden Katalog erreichbar.

## Anhang VII: QMS-Änderungen und Bescheinigungsausstellung

Geplante Änderungen, tatsächliche Anbietermitteilung und Stellenprüfung sind
unterschiedliche Vorgänge. `AIA_ANH_VII_3_4_STELLENKRITERIEN` verlangt die
Untersuchung, die Entscheidung über fortbestehende Erfüllung oder Neubewertung
und deren Mitteilung mit Schlussfolgerungen und Begründung. Eine dokumentierte
Entscheidung bedeutet dabei nicht zwangsläufig eine positive Bewertung.

`P_AIA_ANH_VII_4_6_ERTEILUNG` nennt neben der Bewertungsmitteilung nun ausdrücklich
die tatsächliche Ausstellung und die Bescheinigungsinhalte als getrennte
Erfüllungskriterien. `AIA_ANH_VII_4_6_BESCHEINIGUNGSINHALTE` behandelt bestehende
Gültigkeitsbedingungen und Informationen zur Betriebskontrolle nur soweit
einschlägig; deren Nichtvorliegen muss qualifiziert sein, nicht bloß unbekannt.
Eine positive Bewertung allein belegt weder Ausstellung noch Inhaltsvollständigkeit.

AnhangVII-Verfahrensfolgen sind zusätzlich über eigene Pflichtdatensätze
verknüpft: QMS-Prüfung und Mitteilung, zusätzlicher Technikantrag, spezifische
Trainingsdaten-Ablehnungsbegründung sowie Änderungsprüfung und Ergänzungsweg.
Eine Mitteilung im Ergänzungsweg bleibt auch bei nicht genehmigten Änderungen
erforderlich; eine Ergänzungsausstellung verlangt dagegen die Genehmigung.
Nicht jede Bescheinigungsablehnung verlangt trainingsspezifische Gründe: diese
Folge setzt gerade den nachgewiesenen Trainingsdatenmangel voraus.
Zusatzbeleg-/Anbietertestanforderungen und zusätzliche Tests bei QMS-Audits
sind als Befugnisbedingungen getrennt von zwingenden und tatsächlichen Handlungen
erreichbar. Die materielle Konformitätsbewertung bleibt ein qualifizierter Nachweis.

Tatsächliche Daten-/Modellzugänge, eigene Stellentests, Neutraining und
Systemänderungsmitteilungen sind nun ausdrücklich als Erfüllungskriterien
mit den bestehenden AnhangVII-Pflichten verknüpft. Fernzugangssicherheit gilt
nur soweit einschlägig, Modellzugang bleibt unter dem qualifizierten Schutz
geistigen Eigentums und von Geschäftsgeheimnissen. Neutraining wird weder
aus einem Ablehnungsbescheid noch aus einem künftigen Trainingsplan abgeleitet;
Abschluss und Reihenfolge zum neuen Antrag sind gesondert nachzuweisen.
Interne Kontrolle nach AnhangVI, Weiterführung genehmigter QMS sowie
bewertungsbezogener Standortzugang und periodische Audits haben eigene
Pflichtdatensätze mit getrennten tatsächlichen Erfüllungskriterien.

Artikel43(1) wird über `AIA_043_001_GRUND_A` bis `GRUND_D` sowie
`AIA_043_001_VII_ERFORDERLICH` und `AIA_043_001_WAHL_VI_VII` ausgewertet.
Der sektorale Vorrang nach Absatz3 schließt die beiden Absatz1-Wege aus,
befreit aber nicht von der sektoralen Bewertung. Ein bekannter zwingender
Grund genügt trotz anderer Lücken. Normexistenz, tatsächliche Anwendung,
Spezifikationen und der betroffene Umfang einer Normeinschränkung sind getrennte
lokale Nachweise. Die Regeln wählen nicht selbst für den Anbieter und
bescheinigen keine bereits durchgeführte Konformitätsbewertung.
Der ergänzende Vertrag KONFORMITAETSWEGE.md liegt in den Python-docs bzw.
unter inst/notes des R-Pakets.

Die besonderen Delegationsgegenstände aus Artikel43(5)/(6) und47(5) sind
über GEGENSTAND-Regeln und gesonderte DELEGATIONSWEG-Regeln mit Artikel97
verbunden. Technischer Fortschritt begrenzt die Aktualisierung der AnhängeV
bzw.VI/VII. Eine Erweiterung der Drittbewertung nach43(6) verlangt die
Berücksichtigung der Wirksamkeit interner Kontrolle sowie der verfügbaren
angemessenen Stellenkapazitäten und Ressourcen. Ein passender Gegenstand
ersetzt weder bestehende zeitliche Befugnis noch Konsultation, Mitteilung und
Einwendungsvoraussetzungen. Publikation und weitere Wirksamkeitsfragen bleiben
separat; alle Angaben beziehen sich auf denselben konkreten Rechtsakt.


Kalenderdatumsfelder im Katalog verwenden den Typ `DATUM`: strikt YYYY-MM-DD,
Jahre0001–9999, tatsächliche Kalendergültigkeit nativ geprüft. Beispielsweise
vergleicht `AIA_043_003_ANTRAGSTERMIN` den belegten Zugangstag einschließlich
28.01.2028. Dieser Vergleich beweist weder eine Antragspflicht noch eine Benennung.

Der [Verjährungsvertrag](VERJAEHRUNGSVERTRAG.md) dokumentiert
`berechne_verjaehrung`, Ereignisarten, Unterbrechungen, Hemmungsvereinigung und
die ausdrücklich erforderliche Beginnqualifikation bei F007.

Die [GPAI-Verfahrensrechte](DVO_VERFAHRENSRECHTE.md) erläutern Pflichtauslöser, tatsächliche Erfüllung, Versand-/Empfangswege und verbleibende Rechtsfragen.


## Native ganzzahlige Eingaben

GANZZAHL bezeichnet einen mathematisch ganzzahligen nativen Wert. Python nimmt
`int` und endliche ganzzahlige `float`-Werte an; R nimmt gewöhnliche skalare
`integer`- und `numeric`-Werte an. So werden Python `5.0` und R `5` gleich behandelt.
Die Feldgrenzen gelten weiterhin; der technische sichere Bereich liegt höchstens
bei ±9007199254740991. Boolean, Text, Bruchteile, komplexe Zahlen und nichtendliche
Werte sind keine Ganzzahlen. Benutzerdefinierte numerische Klassen sind nicht Teil
dieses nativen Vertrags. Die Periodenanzahl folgt demselben Vertrag.

Akzeptierte Python-Ganzzahlwerte werden in Ergebnis und Rechenspur kanonisch als
`int` dargestellt; das übergebene Objekt wird nicht geändert. DEZIMAL und
NATURZAHLTEXT bleiben strikte Textverträge, ohne Annahme nativer Gleitkommazahlen.
Der lokale JSON-Leser verlangt weiterhin Zahlentokens ohne Dezimalpunkt oder
Exponent; der Schreiber kann ganzzahlige native Werte kanonisch speichern.

Ein Unternehmensdatensatz kann Felder für mehrere Prüfschritte enthalten.
Vor jedem Aufruf wird er anhand von `eingabevertrag` bzw. dem expliziten lokalen
Feldmapping auf die Felder der betroffenen Regel abgebildet. Zusätzliche Felder
werden vom Prüfkern weiterhin abgelehnt; das verhindert unbemerkte Tippfehler.

[Zusammengesetzte Perioden und1755-Sonderbeginn](PERIODENFRISTEN.md) werden durch `berechne_periodenfrist` mit expliziten fachlichen Grenzen unterstützt.

Die [Geltungsabläufe](GELTUNGSRAHMEN.md) verbinden Rahmen, Sachnorm, Anwendungsbeginn und Bestandsregeln mit einem gemeinsamen lokalen Kontext.

`aggregiere_unternehmensgruppe` aggregiert qualifizierte Verbund-/Partnergruppen mit Schutz gegen doppelte Daten- und Personensegmente. Der vollständige Vertrag steht in [UNTERNEHMENSGRUPPEN.md](UNTERNEHMENSGRUPPEN.md).

Die [Kompetenz-, Normungs- und Evaluationsregeln](KOMPETENZ_NORMUNG_EVALUATION.md) erläutern Artikel4,40/41,78 und112 einschließlich der gesetzlich unterschiedlichen Kalenderzyklen.
