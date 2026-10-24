# P0: weitere Instanzen und Schichten; Testdatenbereinigung

Ausgangsstand `bddd53b0840e3b0fb1f76758b3878f34c22ed62d`, Branch
`codex/search-structure-multilayer-cleanup-2026-10-24`.
Die verbindliche Rangfolge in `weakness_review_2026-10-23.md` setzt
SEARCH-STRUCTURE-01 auf P0. Nach Rundung, Überdeckung und Konturen ergänzt
dieses Teilpaket die ausdrücklich offenen weiteren Instanzen und Schichten.

Der vorhandene Szenenweg verarbeitet jetzt zwei bis vier unterscheidbare
Rechteckkinder in einem Verlaufskreis. Die native Geometrie benötigt weiterhin
beobachtete Abschnitte an allen vier Seiten; Rundung benötigt zwei konsistente
freiliegende Ecken. Mehrere Vordergrundschichten können eine sichtbare Füllung
in getrennte Inseln teilen. Diese werden als gemeinsame Farbhypothese
vorgeschlagen und weiterhin an Inventar, Geometrie und Originalraster geprüft.
Die frühere Mindestquote sichtbarer Fläche war dafür eine zu starke
Vorschlagsbedingung; die unabhängigen Qualitätsgrenzen bleiben unverändert.

Die bestehende Strukturagenda untersucht höchstens 96 Zustände, bei vier
Kindern höchstens 24 Zeichenreihenfolgen, unter demselben Bildbudget. Jede
überlappende Paarung muss ihre sichtbaren Schnittflächen mit der Farbe der
vorderen Instanz erklären. Spätere Schichten werden aus dieser Messung
ausgeschlossen. Alle behaupteten überlappenden Kinder gehören zum selben
zusammenhängenden Überdeckungsgraphen. Unabhängige Objektprüfungen verlangen
nur die Reihenfolge tatsächlich überlappender Paare; die Reihenfolge zweier
getrennter Kinder ist aus dem Bild nicht bestimmbar.

## Nachweise

- Zwölf vor der Runtime-Änderung erzeugte Drei-Instanzen-Eingaben, Seed 713849:
  echte überwachte CLI **0/12 vorher → 12/12 nachher**, jeweils fünf Sekunden
  Bildbudget und Suchseed 17. Die Vergleichseingaben wurden unverändert verwendet.
- Zusätzlicher Seed 927381 mit vier gerundeten, hell umrandeten Instanzen:
  echte CLI **12/12**, einschließlich unabhängiger erneuter Rasterung,
  nativer Objekt-/Relationsprüfung und lokaler/globaler Pixelgates.
- Genau eine gekoppelte gerundete Drei-Instanzen-Vorlage mit heller Kontur,
  Seed 713849, Original plus 16 Plan-B-Varianten: **17/17**.
- Neue Strukturtests: **104 bestanden**, einschließlich fehlender Instanzen,
  gleicher Farben, falscher Anzahl, verdeckter Seiten, Fremdtextur und falscher
  Zeichenreihenfolge. Gemeinsame Struktur-/Regressionsprüfung: **353 bestanden,
  eine wegen fehlender Windows-Symlinkrechte übersprungen**. Die 104 sind in
  den 353 enthalten. Plan-B-Prüfungen: **45 bestanden**.
- Keine vollständige Standardsuite oder neue reale Familienabnahme.
  SEARCH-STRUCTURE-01 bleibt für beliebige Schichten, weitere Primitive und
  unabhängige reale Übertragung offen. Keine neue Symbolvorlage oder Bildkennung.

## Datenlebenszyklus und Wiederholung

`tools.run_seeded_scene_check` speichert den Seed und die Generatoroptionen vor
der Erzeugung in `config/test_run_seeds.jsonl`. Ein eigenes temporäres
Workspace-Verzeichnis enthält Eingaben, Referenzen und tatsächliche
CLI-Ausgaben nur bis zur unabhängigen Nachprüfung. Es wird bei Erfolg,
Fehlschlag, Vorbereitungsfehler und abgefangenem Abbruch entfernt. Unter Windows
funktionieren Konverter-Unterprozesse mit diesen Workspace-Pfaden; systemseitige
Sandbox-Tempverzeichnisse waren für Unterprozesse nicht verlässlich zugänglich.
Ein fehlgeschlagener Versuch bleibt anhand des gespeicherten Seeds wiederholbar.

Pytest räumt sein automatisch erzeugtes Testverzeichnis am Sitzungsende auf.
Plan-B-Läufe behalten standardmäßig Seeds, Quellenhashes, Beschreibung und
kompakte Messwerte; Ursprungsraster und eingebettete Referenz-SVGs entfallen.
Nur das ausdrücklich gewählte `--keep-debug-artifacts` bewahrt Diagnosebilder.
Die bisherigen getrennten `--prepare`/`--inputs`-Schnittstellen bleiben für
gezielte Diagnosen verfügbar; deren explizite Verzeichnisse sind anschließend
mit dem Bereinigungswerkzeug zu entfernen.

`cleanup.bat --apply` bzw. `python -m tools.cleanup_test_data --apply` sichert
Seeds vor dem Entfernen deklarierter Testverzeichnisse. Die sechs jüngsten
reproduzierbaren synthetischen Evidenzpakete bewahren kompakte historische
Ergebnisse und Generatorrezepte statt mehrfacher Eingabe-/Ausgabe-/Logkopien.
Ihre historischen Rohentscheidungen sind danach nicht mehr offline nachprüfbar;
eine Wiederholung erzeugt und prüft neue Ausgaben des aktuellen Codes.
Wo ein historischer Generatorseed nicht dokumentiert war, ist das im Rezept
ausdrücklich ausgewiesen. Benötigte Vertrags-/Evidenzfixtures, reale Quellen,
379 akzeptierte Archivpaare und die Entwicklungsumgebung bleiben erhalten.
Es findet keine Git-Historienumschreibung statt.

Der frühere Kontur-Regressionsfall `probe_08` wird aus Seed 927381 erzeugt;
sein SVG-Hash stimmt exakt mit dem zuvor gespeicherten Fall überein.
Zehn gezielte Lebenszyklustests prüfen Seed-Erhaltung, Quellschutz, Fehler und
Abbruch; die externe Symlinkprobe wird ohne Windows-Symlinkrechte übersprungen.
Weitere Szenen-/Scheduler-/Archivprüfungen bestehen 296 Tests (ein weiterer
Skip); das schnelle core-green-Profil besteht 42 Tests. Die 379 Archivpaare
und alle 758 Bild-/SVG-Prüfsummen sind unverändert.

```powershell
.venv/Scripts/python.exe -m tools.run_seeded_scene_check evaluate_overlap_composition --seed 713849 --children 3
.venv/Scripts/python.exe -m tools.run_seeded_scene_check evaluate_overlap_composition --seed 927381 --children 4 --rounded --outlines
.venv/Scripts/python.exe -m tools.run_seeded_scene_check evaluate_overlap_composition --seed 713849 --children 3 --rounded --outlines --variations
.venv/Scripts/python.exe -m pytest -q tests/test_multilayer_overlap.py tests/test_test_data_lifecycle.py
cleanup.bat --apply
```

## Konkrete Bestandsbereinigung

In drei inventarisierten Durchgängen wurden 2.220 entbehrliche Testziele mit
rund 639.000 Dateien entfernt. Die sechs jüngsten synthetischen Evidenzpakete
enthalten nur noch README, Ignore-Regeln und kompakte historische Prüfwerte.
`config/preserved_test_seeds.json` bewahrt 33.425 Seed-Metadatenquellen;
`config/test_scene_replays.json` enthält die Generatorrezepte.

38 alte Testordner sind auch außerhalb des Sandbox-Kontexts durch Windows
unlesbar (`Access denied`). Sie bleiben bestehen, damit keine ungesicherten
Seeds gelöscht werden. Die konkrete Liste steht in
`config/cleanup_remaining.json`. Vor ihrer Bereinigung ist die Reparatur der
Windows-Zugriffsrechte erforderlich. Drei registrierte Git-Arbeitskopien in
`.tmp` bleiben geschützt. Die aktive `.venv` und ihr globaler Python-Unterbau
bleiben erhalten; der inaktive portable Python-Downloadcache wurde entfernt.
Die umfangreichen Dateiinventare werden nach Abschluss wieder gelöscht.

Nach Entfernung der Rohdaten bestehen 121 gezielte Szenen-/Lebenszyklus-/
Evidenz-/Archivtests (zwei Skips); diese überlappen frühere Prüfblöcke und werden
nicht addiert. CLI-Hilfe, Runtime-ID-Nullprüfung und Syntaxkontrolle bestehen.
