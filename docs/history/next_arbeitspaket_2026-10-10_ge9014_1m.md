# Arbeitspaket – Links-Pfeil mit Verlaufsschaft (2026-10-10)

Branch: `codex/ge9014-quality-2026-10-10`.
Das nächste dokumentierte Ziel `GE9014_1M` und alle 13 Farb-/Größen-Holdouts
bestehen beide unveränderten regulären Gates ohne Pflichtmetrikregression.
Auch die zusätzliche strengere Plan-B-Pixelprüfung besteht für alle 14 JPGs.

## Ursache und allgemeine Korrektur

Die bisherige Beschreibung nannte ein hellgraues Quadrat. Beide XML-Kataloge
beschreiben jetzt eigenständig die nach links gerichtete gefüllte Dreieckspitze,
den schmaleren horizontalen Rechteckschaft mit weißem Abstand und dessen
vertikalen Helligkeitsverlauf. Farben und Geometrie stammen aus dem Raster.

Die vorhandene Pfeilregistrierung normalisiert ausdrücklich beschriebene
Links- und Rechtsrichtungen auf dieselbe Aufwärtsgeometrie. Renderproben werden
in der tatsächlichen Ausgabeorientierung gerendert und für die Suche
zurückgedreht. Die Verlaufsachse erhält auch asymmetrische obere und untere
Farben. Dreieck, Hintergrund und Schaft bleiben native SVG-Elemente;
es gibt keine SVG-Transformationen, Rasterbilder, Runtime-Katalogkennungen
oder hinterlegte Motivvorlagen.

Die horizontale Suche berücksichtigt quadratischen Farbfehler, beobachtete
Konturen und Vordergrundüberdeckung. Sie bleibt auf 121 Renderproben begrenzt
und akzeptiert nur endliche Ergebnisse mit kleinerem primärem Optimierungsfehler
als die Ausgangsregistrierung. Die vertikalen Suchbudgets bleiben erhalten.
Widersprüchliche Farbbeobachtungen am geglätteten Dreiecksrand erhalten eine
zweite Messung mit Nachbarpixeln vor dem Zuschnitt; bereits konsistente
Messungen bleiben erhalten. Sämtliche 28 bisher unterstützten vertikalen
Katalogpfeile behalten exakt ihre frisch erzeugten SVGs.

Lageformulierungen wie „nach rechts und oben verschoben“ ändern die
Pfeilrichtung nicht. Nur diese Lagephrase wird aus der Richtungsprüfung
entfernt; weitere Motivangaben und widersprüchliche Richtungen bleiben
verbindlich. Zusätzliche Rasterobjekte außerhalb des Schafts werden verworfen.

## Frische CLI-Abnahme

Der Originalbeschreibung-Vorlauf wurde vor den Runtime- und XML-Änderungen
mit neutralen Dateinamen eingefroren. Der Reproduktionsrunner prüft Quellhashes,
verwendet getrennte Wegwerfkopien und deaktiviert im Vorlauf ausschließlich die
horizontale Registrierung. Alle 14 Vorlauf-SVGs bleiben bytegleich. Gespeicherte
CLI-Ausgaben werden mit dem Produktionsrenderer neu vermessen; ein unabhängiger
Semantikcheck verlangt Richtung, Dreieck, schmaleren Schaft, Abstand und Verlauf.

| Bild | Mean-Delta² vorher | Mean-Delta² nachher |
|---|---:|---:|
| GE9014_1M | 13053.991211 | 19.939167 |
| GE9014_1S | 10468.363281 | 29.530001 |
| GE9014_2M | 10673.498047 | 28.973333 |
| GE9014_2S | 8242.773438 | 27.593334 |
| GE9014_3M | 8029.864258 | 17.088333 |
| GE9014_3S | 4944.833496 | 26.313334 |
| GE9014_4M | 2905.844238 | 70.270836 |
| GE9014_4S | 2365.189941 | 7.283333 |
| GE9014_5M | 8135.436035 | 36.219166 |
| GE9014_5S | 6257.779785 | 28.693333 |
| GE9014_6M | 15430.596680 | 63.450001 |
| GE9014_6S | 10753.223633 | 25.446667 |
| GE9014_7M | 12533.291992 | 30.445000 |
| GE9014_7S | 11217.660156 | 28.406666 |

**14/14 bestehen Good-Solution- und Quality-Complexity-Gate, null
Pflichtmetrikregressionen; alle 14 bestehen auch die strengeren Pixelgrenzen.**
Zwei unabhängige CLI-Läufe reproduzieren alle 28 SVG-Bytes und Gateentscheidungen.
Verbotene Referenz-SVG-Zugriffe: null.

Eine unabhängig entworfene Vorlage mit abweichender Geometrie und asymmetrischen
Verlaufsfarben besteht Original plus 16 Zufallsvarianten mit Seed `20261010`
(**17/17**) über die echte CLI. Vorlage, Beschreibung, Ursprungsbild und Bericht
sind gespeichert. Qualitätsgrenzen und Vorlage wurden während der Reparatur
nicht verändert. Die anfänglichen Fehler bei Lageformulierungen und
Konturverschiebungen haben eigene Regressionstests.

## Perception-Lerneffekt: generalisiert

Die geprüfte Topologie ist `generalisiert`: Farben, Lage, Auflösung, Pixelphase
und beide horizontalen Pfeilrichtungen sind mit unabhängigen Rasterfällen
geprüft. Umbenennung verändert die Ausgabe nicht. Fehlende Spitze oder Schaft,
Löcher, flache Schaftfarben, zusätzliche Objekte, falsche Verlaufsrichtung,+widersprüchliche Beschreibungen, nicht endliche Fehler und fehlendes Rendering
werden verworfen. Diese Registrierung erschließt weiterhin nur eine gefüllte
Dreieckspitze und einen getrennten, quer schattierten Rechteckschaft auf weißem
Hintergrund. Beliebige Pfeilformen, Hintergründe oder neue Topologien sind damit
nicht als unterstützt belegt; CLI-Restfehlerwarnungen bleiben sichtbar.

## Erfolgsübersicht, Bestandsschutz und nächste Rotation

Die 14 Paare sind mit Beschreibung, Qualitätswerten und Hashes separat in
`artifacts/satisfactory_conversions/` abgelegt; die Sammlung enthält jetzt
**172** Paare. Die zehn schweren Bestandsschutz-, Conversion-Smoke- und
Weak-Family-Tests bestehen, einschließlich der 31 geschützten Varianten.
Die gezielte Pfeilsuite besteht mit **135 Tests**. Die gesamte Erfolgsübersicht
besteht mit **172/172** Review-Pässen. Alle 42 betroffenen Pfeilfälle wurden nach
der letzten Farbmessungskorrektur zusätzlich erneut konvertiert (**42/42**).
Die akzeptierten 158 älteren Indexeinträge bleiben unverändert; die bekannte
Drift von 22 älteren Kompatibilitätsfällen bleibt separat ausgewiesen.
Der kombinierte Nachweis steht in
`artifacts/satisfactory_conversions/recheck_ge9014_2026-10-10.json`.

Der erneuerte Bestandsreview enthält 1.000 Einträge mit 993 renderbaren Paaren;
alle 48 bisherigen Bestenlisteneinträge bleiben unter der unveränderten
Reviewgrenze. Nächste reguläre Rotation: **`GE9012_1M`**, `AC0712_1_S`,
`AC0734_1_S`, `GE9012_2M`, `GE9012_7M`.
Bekannte Graufälle, ältere Archivdrift, der U-Bogen-Stresstest und die beiden
dokumentierten CI-Motivfehler bleiben separate offene Aufgaben.

## Reproduktion

```powershell
$env:IMAGE_CONVERTER_ISOLATE_SVG_RENDER = '0'
.venv/Scripts/python.exe -m tools.run_horizontal_gradient_arrow_recheck artifacts/evaluation/horizontal_gradient_arrow_recheck_v1/manifest.json --output-dir .tmp/horizontal-arrow-reproduction
.venv/Scripts/python.exe -m tools.run_plan_b_variations --svg artifacts/evaluation/horizontal_gradient_arrow_recheck_v1/independent.svg --description-file artifacts/evaluation/horizontal_gradient_arrow_recheck_v1/independent.txt --seed 20261010 --output-dir .tmp/horizontal-arrow-plan-b --keep-debug-artifacts
.venv/Scripts/python.exe -m tools.refresh_satisfactory_archive
.venv/Scripts/python.exe -m tools.recheck_satisfactory_archive --output-dir .tmp/horizontal-arrow-archive
.venv/Scripts/python.exe -m pytest -q tests/test_horizontal_gradient_arrow_runtime.py tests/test_gradient_arrow_runtime.py tests/test_downward_gradient_arrow_runtime.py --basetemp .tmp/horizontal-arrow-tests
$env:RUN_HEAVY_CONVERSION_TESTS = '1'
.venv/Scripts/python.exe -m pytest -q tests/test_satisfactory_regression_battery.py tests/test_conversion_regression_smoke.py tests/test_weak_family_pipeline.py --basetemp .tmp/horizontal-arrow-preservation
$env:RUN_HEAVY_CONVERSION_TESTS = '0'
.venv/Scripts/python.exe -m compileall -q src tests tools
.venv/Scripts/python.exe -m pytest -q --basetemp .tmp/horizontal-arrow-full
.venv/Scripts/python.exe -m src.imageCompositeConverter --help
.venv/Scripts/python.exe -m tools.check_no_new_image_id_hardcoding
```

Für jeden CLI- und Plan-B-Lauf ein frisches Ausgabeverzeichnis verwenden.
Manifest, Vorher-/Nachher-SVGs, Gatebericht, Plan-B-Beleg, vertikaler
Bestandsschutz und Review-Aufruf stehen unter
`artifacts/evaluation/horizontal_gradient_arrow_recheck_v1/`.

## Vollständiger Abschlussnachweis

Der vollständige Standardtestlauf besteht mit **2.207 Tests, 30 bestehenden
Profil-/Windows-Skips und null Fehlern** in **1.313,37 Sekunden**.
Die finalen Pfeilanpassungen, die während des Gesamtlaufs entstanden, wurden
zusätzlich mit den 135 fokussierten Tests, zwei vollständigen CLI-Reproduktionen,
17 unabhängigen Plan-B-CLI-Fällen und der erneuten Konvertierung sämtlicher
42 Pfeilfälle abgesichert. Alle 28 vertikalen SVGs bleiben bytegleich.

Die Erfolgsübersicht besteht mit 172/172 Review-Pässen; alle 158 älteren
Indexeinträge und ihre archivierten Vektoren bleiben unverändert. Die 22
bekannten älteren Kompatibilitätsdrifts bleiben offen. Syntaxprüfung für
`src`, `tests` und `tools`, CLI-Hilfe, Runtime-ID-Nullprüfung und Diff-Prüfung
mit Windows-Zeilenenden bestehen. Quellhashes und sämtliche eingefrorenen
Vorlauf-SVGs wurden abschließend geprüft. Der kompakte Gesamtnachweis steht in
`artifacts/evaluation/horizontal_gradient_arrow_recheck_v1/validation_2026-10-10.json`;
ausführliche lokale Logs unter `.tmp/ge9014-*.log`.
