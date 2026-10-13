# Arbeitspaket – Rechtspfeil auf Verlaufsscheibe (2026-10-13)

Branch: `codex/ge0022-quality-2026-10-13`, Basis `d265e2062`.
Das nach AC1000 dokumentierte Ziel `GE0022.jpg` besteht beide unveränderten
regulären Gates und die strengeren Plan-B-Pixelgrenzen ohne
Pflichtmetrikregression. Das gespeicherte SVG wird zur Abnahme erneut mit
dem Produktionsrenderer gerendert.

## Quellenprüfung und Katalogzuordnung

Die ursprüngliche Beschreibung verweist auf einen gedrehten Aufwärtspfeil
und einen Griff. Das Raster zeigt einen Rechtspfeil aus zusammenhängendem
Rechteckschaft und Dreieckspitze innerhalb einer horizontalen Verlaufsscheibe.
Beide XML-Kataloge ordnen ausschließlich `GE0022.jpg` einer eigenständigen
Beschreibung dieser Primitive zu. Lage, Maße, Farben und Konturen bleiben
Rasterbefunde.

Die neun weiteren Bilder im ursprünglichen GE0022-Eintrag zeigen dagegen
Glocken mit Schallbögen innerhalb einer Verlaufsscheibe: rote, gelbe und
ungefüllte Varianten in drei Größen. Sie sind keine Größen-Holdouts des
Pfeils. Ihre bisherige Beschreibung bleibt erhalten; der offene Folgepunkt
`GE0022-BELL-SOURCE` verlangt eine eigenständige Quellen-/Beschreibungsprüfung
und Qualitätsabnahme. Die Bilder wurden weder verschoben noch als erfolgreiche
Pfeilkonvertierungen gezählt. Das vollständige Inventar mit Quellhashes und
Abmessungen steht in `source_inventory.json`.

## Allgemeine Registrierung

Die bestehende Linkspfeilregistrierung erkennt jetzt die ausdrücklich
beschriebene horizontale Pfeilrichtung. Ein Rechtspfeil wird zur geometrischen
Messung in das vorhandene linke Koordinatensystem gespiegelt. Kreiszentrum,
Pfeilpunkte und Verlaufsrichtung werden beim Aufbau jedes Kandidaten in die
Originalkoordinaten zurückgeführt. Gerendert und bewertet wird unmittelbar
das tatsächliche Ausgabe-SVG. Die Pixelsuche bleibt erhalten.

Beide Richtungen des horizontalen Helligkeitsverlaufs sind zulässig. Ihre
Endfarben werden unabhängig von der Pfeilrichtung aus dem Raster gemessen.
Widersprüchliche oder fehlende Pfeilrichtungen, falsche Rastertopologien,
Zusatzobjekte und Lücken werden weiterhin verworfen. Die Ausgabe enthält
Hintergrundrechteck, Verlaufskreis und ein zusammenhängendes Pfeilpolygon;
keine Transformation, Konturkopie, Rastereinbettung oder Motivkennung.

Das Plan-B-Prüfwerkzeug verwendet bereits geladene Renderbibliotheken direkt,
statt vor jedem Suchkandidaten erneut die optionalen Bibliotheksverzeichnisse
zu prüfen. Der Renderer und sämtliche Qualitätsgrenzen bleiben identisch.
Die nachfolgende Wiederholung reproduziert auch die zuvor gemessenen Ergebnisse.

## CLI-Abnahme und unabhängige Fälle

Der tatsächliche neutral benannte Originalbeschreibungs-Vorlauf wurde vor
der Runtime- und XML-Änderung eingefroren. Der Mean-Delta²-Wert sinkt von
**10954.268555 auf 198.207550**. Beide regulären Gates und sämtliche strengeren
Pixelgrenzen bestehen; null Pflichtmetrikregressionen und null verbotene
Referenz-SVG-Zugriffe. Die unabhängige Semantikprüfung verlangt explizit einen
Rechtspfeil innerhalb einer umrandeten Kreisscheibe mit nativem Verlauf.

Zwei CLI-Abnahmen reproduzieren Vorlauf, finales SVG, Metriken und Gates.
Zwei getrennte Abnahmen verwenden den echten Katalognamen und den vollständigen
Originalkatalog aus dem Basiscommit. Die originale Runtime wird im isolierten
Vorlauf geladen. Der finale Vektor stimmt bytegleich mit der neutralen Ausgabe
überein; die eigenständige Katalogbaseline wird ebenfalls eingefroren und
wiederholt. Beide Baseline-Kontexte bleiben im Nachweis getrennt.

Eine unabhängig konstruierte grüne Rechtspfeil-Scheibe verändert Auflösung,
Pose, Größenverhältnisse und Farbpalette. Zwei echte CLI-Prüfungen mit Seed
`20261013` bestehen jeweils Original plus 16 Zufallsvarianten: **17/17**.
Eingangs- und Ausgangshashes, Metriken, Komplexität und Gateentscheidungen
stimmen überein. Zusätzliche Rastertests prüfen halbe und doppelte Auflösung,
Lageverschiebungen, umgekehrten Verlauf, Umbenennung und Negativfälle.
Alle bisherigen Linkspfeiltests bestehen ebenfalls.

## Bestandsschutz und nächste Rotation

Die Erfolgsübersicht enthält **237 Paare**. Alle 236 bisherigen Indexeinträge
bleiben identisch. Die erneute Archivprüfung besteht in sechs getrennten
Prozessen mit **237/237**. Alle 236 bisherigen Mean-Delta²-Werte und die 22
bekannten älteren Kompatibilitätsdrifts bleiben exakt unverändert.
Die finale Standard-, Smoke- und Archivprüfung wird in
`artifacts/evaluation/right_disk_arrow_recheck_v1/validation_2026-10-13.json`
mit tatsächlichen Testzahlen und Source-Hashes dokumentiert.

Der vollständige finale Standardlauf besteht mit **2.530 Tests und 30
bestehenden Skips, null Fehlern**. Die fokussierte Pfeil-/Plan-B-Suite besteht
mit 92 Tests, die AC08-/AC0100-Smoke-Prüfung mit zwei Tests. Die vorhandene
Linkspfeil-CLI-Abnahme reproduziert alle acht eingefrorenen Vorher-/Nachher-SVGs
und besteht mit 4/4 regulären und strengeren Gates. Syntaxprüfung, CLI-Hilfe,
Runtime-ID-Nullprüfung, Artefakthashes und Diff-Prüfung bestehen. Zwei frühe
Teststarts wurden während der Laufzeitdiagnose unterbrochen und zählen nicht
als Abnahme; beide anschließend abgeschlossenen langsamen Testsuiten waren
ebenfalls grün. Der finale 92-Test-Lauf prüft die Bibliothekswiederverwendung.

Der erneuerte Review umfasst 1.000 Einträge und 993 renderbare Paare; alle
48 bisherigen Bestenlisteneinträge bleiben unter der unveränderten Grenze.
Nur der abgenommene Pfeil wird zusätzlich ausgeschlossen. Es folgen
**`GE9024_1M`**, `GE0300`, `b_heating1`, `AC0421_1_S` und `GE0306`.

```powershell
$env:IMAGE_CONVERTER_ISOLATE_SVG_RENDER = '0'
.venv/Scripts/python.exe -m tools.run_disk_arrow_recheck artifacts/evaluation/right_disk_arrow_recheck_v1/manifest.json --output-dir .tmp/right-arrow-reproduce
.venv/Scripts/python.exe artifacts/evaluation/right_disk_arrow_recheck_v1/recheck_catalog_context.py --output-dir .tmp/right-arrow-catalog-reproduce
.venv/Scripts/python.exe -m tools.run_plan_b_variations --svg artifacts/evaluation/right_disk_arrow_recheck_v1/independent.svg --description-file artifacts/evaluation/right_disk_arrow_recheck_v1/independent.txt --seed 20261013 --output-dir .tmp/right-arrow-plan-b-reproduce --keep-debug-artifacts
.venv/Scripts/python.exe -m tools.recheck_satisfactory_archive --output-dir .tmp/right-arrow-archive-reproduce --max-cases-per-worker 48
$env:RUN_HEAVY_CONVERSION_TESTS = '0'
.venv/Scripts/python.exe -m pytest -q --basetemp .tmp/right-arrow-tests-reproduce
.venv/Scripts/python.exe -m compileall -q src tests tools
.venv/Scripts/python.exe -m src.imageCompositeConverter --help
.venv/Scripts/python.exe -m tools.check_no_new_image_id_hardcoding
git -c core.whitespace=cr-at-eol diff --check
```

CLI-Prüfungen benötigen frische Ausgabeverzeichnisse. Das Paket versioniert
Manifest, Baseline- und finale Vektoren, Gateberichte, Quelleninventar,
unabhängige Eingaben und Vektoren sowie Wiederholungsnachweise. Vollständige
Diagnoseläufe bleiben lokal unter `.tmp/right-arrow-*` erhalten.
