# euaiact – Python

Native, lokale Rechen- und Logikregeln zum EU AI Act. **Version 0.1.0 mit ausdrücklich dokumentierten Auswertungsgrenzen.** Der Kern prüft einzelne sachliche
Tatbestände; eine positive oder negative Entscheidung ist keine umfassende
Konformitätsaussage. Quellenfassung und Bearbeitungsstatus sind explizit.

```python
from euaiact import pruefe_tatbestand

ergebnis = pruefe_tatbestand(
    "AIA_051_002",
    {"trainings_flops": "10000000000000000000000001"},
    quellenfassung="EUAIACT_2026_07_27",
)
assert ergebnis["wert"] is True
```

Der Kern benötigt keine Netzwerkverbindung, keine PDF-Datei und keine externen
Laufzeitpakete. Unternehmensdaten werden als eigene Dictionaries übergeben.
Fehlende Angaben bleiben unbekannt; Werte werden nicht automatisch geraten.

Lokale Installation aus einem bereitgestellten Wheel:

```sh
python -m pip install --no-index --no-deps /lokale/pakete/euaiact-0.1.0-py3-none-any.whl
```

Für einen Build aus dem Source-Archiv müssen zusätzlich die in `pyproject.toml`
genannten Buildwerkzeuge lokal vorhanden sein; danach mit `--no-index`
und `--no-build-isolation` installieren. Der Kern hat keine Laufzeitabhängigkeiten.
Der bisherige lokale Nachweis verwendet Python 3.10 unter Linux. Weitere Versionen
und Betriebssysteme sind noch nicht durch eine Supportmatrix abgenommen.

Die [API-Dokumentation](docs/API.md) beschreibt Rechen-, Frist-, Zeit- und
Tatbestandsfunktionen sowie lokale JSON-Adapter. `eingabevertrag(regel_id)` liefert
auch die Felder referenzierter Regeln. Eigene Namenskonventionen können mit
`ordne_daten_zu` explizit zugeordnet werden; es werden keine Bewertungen geraten.

Die acht [synthetischen Unternehmensszenarien](examples/unternehmen_synthetisch.json)
laufen nach Installation mit `python examples/unternehmen.py`. Der Code verwendet
dieselben öffentlichen APIs für alle Unternehmen. `--ausgabe /lokaler/neuer_pfad.json`
exportiert Ergebnisse einschließlich Herkunft der Feldzuordnung. Dateien werden
nicht überschrieben. Rollen, Organisationsbezüge und fachliche Bewertungen sind
Beispieldaten, die beim Einsatz durch begründete eigene Angaben zu ersetzen sind.

Lokale Entwicklung: `python -m pytest` und `ruff check .`. Tests benötigen pytest und jsonschema;
Buildwerkzeuge und Testabhängigkeiten sind separat lokal bereitzustellen. Die
beigefügten Ressourcen und Fixtures machen dieses Repository eigenständig testbar.

Copyright RiskDataScience GmbH. Ansprechpartner: Dr. Dimitrios Geromichalos,
riskdatascience@web.de. Apache License 2.0. Herausgeber: https://riskdatascience.net.

`tabellen_katalog()` und `tabelle_info(tabellen_id)` stellen fünf lokale,
versionierte Anhangtabellen mit 77 Einträgen bereit: Rechtsakte, Deliktsgruppen,
IT-Systeme, GPAI-Kriterien und Notifizierungscodes. Sie enthalten Quellennachweise
und Grenzen; Listenmitgliedschaft allein ist keine Anwendbarkeitsentscheidung.


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

## Eigenständige kontinuierliche Prüfung

Der Workflow `.github/workflows/check.yml` arbeitet im jeweiligen einzelnen
GitHub-Repository. Er benötigt weder das andere Sprachpaket noch den
Factory-Quellbaum. Die Einrichtung der Entwicklungswerkzeuge in GitHub Actions
benötigt Netz; Bibliotheksbetrieb und Unternehmensbeispiele bleiben lokal.
Die Workflows veröffentlichen keine Pakete und haben nur Leserechte.

Python prüft auf Linux die Mindestversion 3.10 und Version 3.14, auf Windows und
macOS 3.14. `python tools/check_distributions.py` baut Wheel/sdist, prüft die
Metadaten und installiert beide getrennt ohne Indexzugriff. Tests laufen aus
den sdist-Inhalten außerhalb des Quellbaums; der Importort wird geprüft. Unter
Linux sperrt seccomp zusätzlich Netz-Sockets während Tests und Beispielen.
Andere Betriebssysteme erhalten dadurch keinen behaupteten seccomp-Nachweis.
Die Testwerkzeuge müssen vorher lokal bereitstehen: build, setuptools>=61,
wheel, twine, pytest und jsonschema. Ein optionaler `--test-filter` dient nur
gezielten lokalen Wiederholungen; CI verwendet die vollständige vorhandene Suite.

R prüft Linux/release, oldrel-1, devel und die Mindestreihe 4.1 sowie
Windows/release und macOS/release mit R CMD check --as-cran ohne PDF-Handbuch.
Auch Hinweise führen zum Fehlschlag. Anschließend werden die installierten
synthetischen Unternehmensbeispiele aus einem temporären Arbeitsverzeichnis
ausgeführt. R benötigt dafür keine Python-Installation.

Die Konfiguration ist kein Nachweis bereits ausgeführter GitHub-Jobs.
Plattformübergreifende CI-Ergebnisse liegen erst nach tatsächlicher Ausführung
in den künftigen Repositories vor.

Weitere lokale Fachverträge: [Jahresarbeitseinheiten](docs/JAHRESARBEITSEINHEITEN.md), [Begriffsabgrenzungen](docs/BEGRIFFSABGRENZUNGEN.md) und [Gremiumsverfahren](docs/GREMIUMSVERFAHREN.md).

[Reallabore, Realtests und Behördenverfahren](docs/REALLABORVERFAHREN.md).

[Marktaufsicht, Verfahrensnachweise und Zwangsgeldgrenzen](docs/MARKTAUFSICHT.md).

[Betrieb und Versionierung](docs/BETRIEB_UND_VERSIONIERUNG.md) erläutert Integration,
Updates und den Prüfungsumfang; [offene Fachfragen](docs/OFFENE_FACHFRAGEN.md)
begrenzen die automatisch bestimmbaren Ergebnisse.
