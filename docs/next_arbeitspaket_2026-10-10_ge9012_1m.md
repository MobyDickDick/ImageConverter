# Arbeitspaket – Rechtspfeil mit Verlaufsschaft (2026-10-10)

Branch: `codex/ge9012-quality-2026-10-10`.
Das nächste dokumentierte Ziel `GE9012_1M` und alle 13 Farb-/Größen-Holdouts
bestehen beide unveränderten regulären Qualitätsgates ohne Pflichtmetrikregression.
Alle 14 JPGs bestehen zusätzlich die strengeren Plan-B-Pixelgrenzen.

## Ursache und Korrektur

Die bisherige Beschreibung nannte ein hellgraues Quadrat. Beide XML-Kataloge
beschreiben jetzt eigenständig die nach rechts gerichtete gefüllte Dreieckspitze,
den schmaleren horizontalen Rechteckschaft mit weißem Abstand und dessen
vertikalen Helligkeitsverlauf. Die Beschreibung enthält keine festen Farben,
Koordinaten oder Verweise auf andere Katalogbilder.

Die vorhandene allgemeine Pfeilregistrierung unterstützt diese Richtung bereits.
Sie bestimmt Geometrie und Farben aus dem Eingabebild und verfeinert die Parameter
über gerenderte Kandidaten. Deshalb benötigt dieses Paket **keine Runtime-Änderung**.
Die Ausgabe enthält einen Hintergrund, eine Dreieckspitze und einen Schaft mit
nativem SVG-Verlauf. Referenz-SVGs, Rastereinbettungen und Motivkennungen im
Runtime-Code sind keine Konvertierungsquellen.

## Frische CLI-Abnahme

Vor der XML-Korrektur wurde für sämtliche 14 Originalbeschreibungen ein frischer
CLI-Vorlauf mit neutralen Dateinamen eingefroren. Zwei unabhängige Abnahmen
verwenden getrennte Wegwerfkopien; Quellhashes und eingefrorene Vorlauf-SVGs
werden geprüft. Der vorhandene horizontale Recheck-Runner wird mit der Richtung
`right` wiederverwendet. Seine Vorlauf-Deaktivierung der horizontalen Registrierung
ist hier wirkungslos, weil die ursprüngliche Quadratbeschreibung keinen Pfeil nennt.
Die Runtime ist gegenüber dem echten Vorlauf unverändert.

Gespeicherte CLI-SVGs werden mit dem Produktionsrenderer neu vermessen. Der
unabhängige Semantikcheck verlangt einen Rechtspfeil, eine gefüllte Dreieckspitze,
einen getrennten schmaleren Schaft und einen quer zum Schaft verlaufenden Verlauf.

| Bild | Mean-Delta² vorher | Mean-Delta² nachher |
|---|---:|---:|
| GE9012_1M | 13193.511719 | 18.595833 |
| GE9012_1S | 10873.856445 | 28.016666 |
| GE9012_2M | 12705.636719 | 24.358334 |
| GE9012_2S | 8241.950195 | 27.756666 |
| GE9012_3M | 8037.081055 | 15.338333 |
| GE9012_3S | 4970.229980 | 26.023333 |
| GE9012_4M | 2891.079102 | 18.195833 |
| GE9012_4S | 2369.983398 | 6.770000 |
| GE9012_5M | 8169.044922 | 43.205833 |
| GE9012_5S | 6317.890137 | 29.356667 |
| GE9012_6M | 15386.639648 | 60.480835 |
| GE9012_6S | 10695.030273 | 25.469999 |
| GE9012_7M | 12343.563477 | 30.165833 |
| GE9012_7S | 7442.753418 | 28.523333 |

**14/14 bestehen Good-Solution- und Quality-Complexity-Gate, null
Pflichtmetrikregressionen. Auch die strengere Pixelprüfung besteht 14/14.**
Beide CLI-Abnahmen erzeugen identische 28 Vorher-/Nachher-SVGs und identische
Gateberichte. Verbotene Referenz-SVG-Zugriffe: null. Beide Produktionskataloge
liefern für alle Varianten genau die abgenommene Beschreibung.

## Unabhängige Prüfung und Generalisierung

Eine unabhängig entworfene Vorlage mit anderer Geometrie, Pixelphase und
asymmetrischen Verlaufsfarben besteht mit Seed `20261010` Original plus 16
Zufallsvarianten über die echte CLI (**17/17**). Die Vorlage ist eine Testquelle;
der Konverter erhält jeweils nur deren Rasterbild und sprachliche Beschreibung.
Vorlage, Beschreibung, Ursprungsbild und kompakter Bericht sind gespeichert.

Der Perception-Stand dieser Topologie bleibt `generalisiert`; dieses Paket
aktiviert vorhandene Unterstützung durch zutreffende Beschreibungen. Die
erweiterte Pfeilsuite besteht mit **149 Tests**, darunter alle 14 neuen realen
Farb-/Größenfälle. Bereits vorhandene Prüfungen sichern beide horizontalen
Richtungen, unabhängige Farben, Auflösungen, Lageänderungen und widersprüchliche
Beschreibungen sowie fehlende oder zusätzliche Rasterobjekte ab.
Es ist keine neue beliebige Pfeiltopologie erschlossen. Die Unterstützung
bleibt auf Dreieckspitze und getrennten Rechteckschaft mit Querverlauf auf
weißem Hintergrund begrenzt. CLI-Restfehlerwarnungen bleiben sichtbar.

## Erfolgsübersicht, Bestandsschutz und nächste Rotation

Die 14 Paare sind mit Beschreibungen, Qualitätswerten und Hashes separat unter
`artifacts/satisfactory_conversions/` abgelegt. Die Sammlung enthält jetzt
**186** Paare; alle 172 älteren Indexeinträge bleiben unverändert.
Die erneute Konvertierung sämtlicher archivierter Eingaben besteht mit
**186/186 Review-Pässen**. Die bekannten höheren Fehlerwerte von 22 älteren
Kompatibilitätsfällen bleiben unverändert separat ausgewiesen.
Die zehn schweren Bestandsschutz-, Conversion-Smoke- und Weak-Family-Tests
bestehen, einschließlich der 31 geschützten Varianten.

Der erneuerte Bestandsreview enthält 1.000 Einträge mit 993 renderbaren Paaren;
alle 48 bisherigen Bestenlisteneinträge bleiben unter der unveränderten
Reviewgrenze. Alle 14 erledigten Varianten werden aus der Rotation ausgeschlossen.
Nächste reguläre Rotation: **`AC0712_1_S`**, `AC0734_1_S`, `GE9021_1M`,
`SE0081`, `GE0039_M`.
Bekannte Graufälle, ältere Archivdrift, der U-Bogen-Stresstest und die beiden
dokumentierten CI-Motivfehler bleiben separate offene Aufgaben.

## Reproduktion

```powershell
$env:IMAGE_CONVERTER_ISOLATE_SVG_RENDER = '0'
.venv/Scripts/python.exe -m tools.run_horizontal_gradient_arrow_recheck artifacts/evaluation/rightward_gradient_arrow_recheck_v1/manifest.json --output-dir .tmp/rightward-arrow-reproduction
.venv/Scripts/python.exe -m tools.run_plan_b_variations --svg artifacts/evaluation/rightward_gradient_arrow_recheck_v1/independent.svg --description-file artifacts/evaluation/rightward_gradient_arrow_recheck_v1/independent.txt --seed 20261010 --output-dir .tmp/rightward-arrow-plan-b --keep-debug-artifacts
.venv/Scripts/python.exe -m tools.refresh_satisfactory_archive
.venv/Scripts/python.exe -m tools.recheck_satisfactory_archive --output-dir .tmp/rightward-arrow-archive
.venv/Scripts/python.exe -m pytest -q tests/test_horizontal_gradient_arrow_runtime.py tests/test_gradient_arrow_runtime.py tests/test_downward_gradient_arrow_runtime.py --basetemp .tmp/rightward-arrow-tests
$env:RUN_HEAVY_CONVERSION_TESTS = '1'
.venv/Scripts/python.exe -m pytest -q tests/test_satisfactory_regression_battery.py tests/test_conversion_regression_smoke.py tests/test_weak_family_pipeline.py --basetemp .tmp/rightward-arrow-preservation
$env:RUN_HEAVY_CONVERSION_TESTS = '0'
.venv/Scripts/python.exe -m compileall -q src tests tools
.venv/Scripts/python.exe -m pytest -q --basetemp .tmp/rightward-arrow-full
.venv/Scripts/python.exe -m src.imageCompositeConverter --help
.venv/Scripts/python.exe -m tools.check_no_new_image_id_hardcoding
```

Für jeden CLI- und Plan-B-Lauf ein frisches Ausgabeverzeichnis verwenden.
Manifest, Vorher-/Nachher-SVGs, Gatebericht, unabhängiger Plan-B-Beleg,
Reproduzierbarkeitsbericht und Review-Aufruf stehen unter
`artifacts/evaluation/rightward_gradient_arrow_recheck_v1/`.

## Vollständiger Abschlussnachweis

Der vollständige Standardtestlauf besteht mit **2.222 Tests, 30 bestehenden
Profil-/Windows-Skips und null Fehlern** in **1.177,91 Sekunden**.
Die fokussierte Pfeilsuite besteht mit 149 Tests in 49,27 Sekunden; die zehn
Bestandsschutz-/Smoke-Tests bestehen in 56,33 Sekunden. Die unabhängige CLI-
Plan-B-Abnahme besteht 17/17, beide regulären und die strengeren JPG-Gates 14/14.

Die erneute Archivkonvertierung besteht mit 186/186 Review-Pässen. Alle 172
älteren Indexeinträge und die 22 bekannten höheren Kompatibilitätsfehler bleiben
unverändert. Der Bericht steht unter
`artifacts/satisfactory_conversions/recheck_ge9012_2026-10-10.json`.
Syntaxprüfung für `src`, `tests` und `tools`, CLI-Hilfe, Runtime-ID-Nullprüfung,
Quellhashes, eingefrorene Vorlauf-SVGs und Diff-Prüfung mit Windows-Zeilenenden
bestehen. Der kompakte Gesamtnachweis steht unter
`artifacts/evaluation/rightward_gradient_arrow_recheck_v1/validation_2026-10-10.json`;
ausführliche lokale Logs unter `.tmp/ge9012-*.log`.
