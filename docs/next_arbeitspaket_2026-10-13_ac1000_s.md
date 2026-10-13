# Arbeitspaket – Kreisscheibe mit M (2026-10-13)

Branch: `codex/ac1000-quality-2026-10-13`.
Das nach AC0920 dokumentierte Ziel `AC1000_S` und beide Größen-Holdouts
bestehen beide unveränderten regulären Gates sowie alle strengeren
Plan-B-Pixelgrenzen ohne Pflichtmetrikregression.

## Ursache und allgemeine Korrektur

Die bisherige Beschreibung nennt Kreis, Grau und M, beschreibt jedoch die
gefüllte Kreisscheibe, die Kontur, die Schrift und den weißen Hintergrund
nicht eindeutig. Beide XML-Kataloge enthalten jetzt eine eigenständige
Primitivbeschreibung. Maße, Lage und Farben werden aus dem Raster ermittelt;
auch die unterschiedlich gefärbten Größenvarianten nutzen denselben Text.

Die vorhandene allgemeine Kreis-/Textregistrierung reicht für S und M aus.
Beim eng beschnittenen großen Raster enthält der beobachtete Außenradius
bereits die Kontur. Der anfängliche Kandidat addierte deren halbe Breite
noch einmal und verletzte die Bildgrenze. Der Startkandidat berücksichtigt
jetzt die vollständige Konturbreite und bleibt um eine SVG-Rundungseinheit
innerhalb des verfügbaren Radius. Ein unabhängiger Beschnitttest belegte auch
die andernfalls mögliche Ablehnung durch Gleitkommaauslöschung.

Die begrenzte Optimierung und sämtliche Annahme-, Semantik- und Pixelgrenzen
bleiben erhalten. Die Ausgabe besteht aus Hintergrundrechteck, Kreis und
nativem SVG-Text M. Dateinamen, Katalogkennungen, gespeicherte SVGs und
Konturkopien sind keine Runtime-Wissensquellen. Der Nachweis betrifft weiterhin
einen beschriebenen dunklen Einzelbuchstaben in einer hellen, einfarbigen,
umrandeten Kreisscheibe auf weißem Hintergrund, keine allgemeine OCR.

## Frische CLI-Abnahme und Wiederholung

Die drei neutral benannten Originalbeschreibungs-Vorläufe wurden tatsächlich
vor der Runtime- und Beschreibungsänderung eingefroren. Beide Folgeabnahmen
verwenden Wegwerfkopien, prüfen Quellhashes und sperren Referenz-SVG-Zugriffe.
Die originalen Vorläufe und alle finalen SVGs, Metriken und Gates werden
reproduziert. Bewertet wird das auf Platte gespeicherte SVG nach erneutem
Rendern mit dem Produktionsrenderer.

| Bild | Mean-Delta² vorher, neutral | Mean-Delta² nachher |
|---|---:|---:|
| AC1000_S | 11123.106445 | 496.119995 |
| AC1000_M | 7667.182617 | 591.427490 |
| AC1000_L | 8099.953125 | 685.416687 |

**3/3 bestehen beide regulären Gates und sämtliche strengeren Pixelgrenzen;
null Pflichtmetrikregressionen und null Referenz-SVG-Zugriffe.** Die unabhängige
Semantikprüfung verlangt den gefüllten umrandeten Kreis, das exakte native M,
zentrale Textlage, Kontrastfarben und passende Abmessungen. Der Prüfwerkzeug-
vertrag verwendet jetzt den im Manifest angegebenen Buchstaben; ältere
Q-Manifeste behalten ihren bisherigen Vertrag.

Eine eigene Abnahme verwendet echte Katalognamen und den vollständigen
Originalkatalog aus Commit `65ae083ea`. Der Vorlauf verwendet auch dessen
ursprüngliches Kreis-/Textmodul im isolierten Worker. Die Originalbeschreibung
aktiviert die neue Registrierung nicht. Die Katalogvorläufe sind wegen des
alten Dispatchs nicht mit den neutralen Vorläufen gleichzusetzen:
`5674.813477`, `6890.100098` und `6890.640137` für S, M und L. Diese Baseline
wird separat eingefroren und wiederholt. Alle drei finalen Katalog-SVGs sind
bytegleich mit der neutralen Ausgabe; beide regulären und strengeren Gates
bestehen auch im vollständigen Katalogkontext. Zufällige Ausgabevariation
bleibt in sämtlichen Abnahmen deaktiviert.

## Unabhängige Fälle und Bestandsschutz

Eine unabhängig konstruierte grüne M-Kreisscheibe mit anderer Geometrie,
Farbpalette und Auflösung besteht mit Seed `20261013` zweimal die echte
CLI-Abnahme: jeweils Original plus 16 Zufallsvarianten, **17/17**. Eingangs-
und Ausgangshashes, Pixelmessungen, Komplexität und Gateentscheidungen sind
identisch. Zusätzliche Rastertests prüfen M bei drei Auflösungen und engem
Beschnitt. Die bisherigen Q/R/P/D/A- und Negativfälle bleiben erhalten.

Die Erfolgsübersicht enthält **236 Paare**. Alle 233 bisherigen Indexeinträge
bleiben identisch. Die getrennte finale Archivprüfung besteht mit **236/236**;
alle 233 bisherigen erneut gemessenen Pixelfehler und die 22 bekannten älteren
Kompatibilitätsdrifts bleiben exakt unverändert. Die finale Testabnahme sowie
Source-Hashes sind in `validation_2026-10-13.json` dokumentiert. Frühe
Diagnoseläufe bleiben von den finalen Prüfungen getrennt. Die erste
Beschnittprüfung fand die oben korrigierte Rundungsablehnung. Die erste
Archivprüfung überschnitt sich mit dem Austausch des finalen L-Vektors und
wurde von der Hashprüfung des archivierten SVGs abgelehnt; die komplette Archivprüfung wurde
nach Stabilisierung der Artefakte erfolgreich wiederholt.

Die finale fokussierte Suite besteht mit **42 Tests**, die AC08-/AC0100-
Smoke-Prüfung mit zwei Tests. Der vor der letzten Rundungskorrektur gestartete
Standardlauf besteht mit 2.506 Tests und 30 bestehenden Skips; sein einziges
Fail ist der bereits behobene 60-Pixel-Beschnittfall im zuvor importierten
Runtime-Modul. Die vollständige finale 42-Test-Nachprüfung und eine weitere
Einzelprüfung nach Ende des Standardlaufs bestehen. Damit besitzen **2.507
unterschiedliche Standardfälle** bestandene Nachweise; **null ungelöste Fehler**.
Der rohe Standardbericht behält seinen tatsächlichen Fail. Syntaxprüfung,
CLI-Hilfe, Runtime-ID-Nullprüfung und Diff-Prüfung bestehen. Die Abdeckung,
Diagnose- und Nachläufe sowie die finalen Source-Hashes stehen im maschinenlesbaren
Abnahmebericht.

## Nächste Rotation und Reproduktion

Der erneuerte Review umfasst 1.000 Einträge und 993 renderbare Paare. Alle
48 bisherigen Bestenlisteneinträge bleiben unter der unveränderten Grenze.
Bisherige Ausschlüsse und alle drei erledigten M-Größen werden fortgeschrieben.
Es folgen **`GE0022`**, `GE9024_1M`, `GE0300`, `b_heating1` und `AC0421_1_S`.

```powershell
$env:IMAGE_CONVERTER_ISOLATE_SVG_RENDER = '0'
.venv/Scripts/python.exe -m tools.run_labeled_disk_recheck artifacts/evaluation/motor_disk_recheck_v1/manifest.json --output-dir .tmp/motor-disk-reproduce
.venv/Scripts/python.exe artifacts/evaluation/motor_disk_recheck_v1/recheck_catalog_context.py --output-dir .tmp/motor-disk-catalog-reproduce
.venv/Scripts/python.exe -m tools.run_plan_b_variations --svg artifacts/evaluation/motor_disk_recheck_v1/independent.svg --description-file artifacts/evaluation/motor_disk_recheck_v1/independent.txt --seed 20261013 --output-dir .tmp/motor-disk-plan-b-reproduce --keep-debug-artifacts
.venv/Scripts/python.exe artifacts/evaluation/labeled_disk_recheck_v1/recheck_archive_families.py --output-dir .tmp/motor-disk-archive-reproduce
$env:RUN_HEAVY_CONVERSION_TESTS = '0'
.venv/Scripts/python.exe -m pytest -q --basetemp .tmp/motor-disk-tests-reproduce
.venv/Scripts/python.exe -m compileall -q src tests tools artifacts/evaluation/motor_disk_recheck_v1
.venv/Scripts/python.exe -m src.imageCompositeConverter --help
.venv/Scripts/python.exe -m tools.check_no_new_image_id_hardcoding
git -c core.whitespace=cr-at-eol diff --check
```

CLI-Rechecks benötigen frische Ausgabeverzeichnisse. Manifest, Vorläufe,
finale Vektoren, beide regulären und die strengeren Gates, Katalogkontext,
unabhängige Vorlage und wiederholte Plan-B-Messungen stehen unter
`artifacts/evaluation/motor_disk_recheck_v1/`.
