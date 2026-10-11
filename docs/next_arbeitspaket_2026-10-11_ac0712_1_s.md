# Arbeitspaket – Quadrat mit linkem Griff, Strich und Punkt (2026-10-11)

Branch: `codex/ac0712-quality-2026-10-11`.
Das nächste dokumentierte Ziel `AC0712_1_S` und fünf Farb-/Größen-Holdouts
bestehen beide unveränderten regulären Gates ohne Pflichtmetrikregression.
Alle sechs JPGs bestehen zusätzlich die strengeren Plan-B-Pixelgrenzen.

## Ursache und allgemeine Korrektur

Die ursprüngliche Beschreibung verwies auf eine andere Katalogform und
verschwieg die Innenmarkierungen. Beide XML-Kataloge beschreiben jetzt
eigenständig Quadrat, Kontur, mittigen linken Griff, den schrägen Strich von
rechts oben nach links unten und den quadratischen Punkt links am unteren Ende.
Geometrie, Farben und Konturbreiten stammen aus dem Rasterbild.

Der vorhandene Parser nahm beim Linksgriff bisher ein `T` an. Explizit
beschriebene Strich-/Punktmarkierungen erhalten jetzt eine Geometrie ohne
Text; die bisherige explizite Texttopologie bleibt erhalten. Die allgemeine
Quadrat-/Griffregistrierung normalisiert den Linksgriff auf die vorhandene
Rechtsgriffsuche, beobachtet die Innenmarkierungen aber in den ursprünglichen
Achsen. Die Rückabbildung schreibt native Vektorkoordinaten. Das SVG enthält
ein Rechteck und drei Pfade, ohne Rastereinbettung oder SVG-Transformation.
Runtime-Katalogkennungen und gespeicherte Motivvorlagen werden nicht ergänzt.

Eine bis zum Bildrand reichende Quadratfläche führte im mittleren roten JPG
zu einer falschen Konturfarbannahme: Die Zweipixelprobe enthielt schon Füllfarbe.
Die Linksgriffsuche vergleicht daher eine zweite, ebenfalls aus dem Raster
gemessene Randfarbe. Der gerenderte quadratische Pixelfehler entscheidet über
die bessere Ausgangsannahme. Einschließlich dieser einen Zusatzprobe bleibt
die Suche auf höchstens 1.442 Renderbewertungen begrenzt.

## Frische CLI-Abnahme

Vor jeder Runtime- und XML-Änderung wurden sechs Originalbeschreibung-Ausgaben
mit neutralen Dateinamen eingefroren. Der Recheck-Runner verwendet getrennte
Wegwerfkopien, prüft Quellhashes und deaktiviert im Vorlauf ausschließlich die
neue Linksgriffregistrierung. Die ursprünglichen Beschreibungen enthalten keine
Strich-/Punktangabe; alle sechs echten Vorlauf-SVGs bleiben bytegleich.
Die Qualitätsmessung rendert das gespeicherte End-SVG mit dem Produktionsrenderer
erneut. Der unabhängige Semantikcheck verlangt Linksgriff, Quadrat und beide
Innenmarkierungen in ihrer beschriebenen Lage.

| Bild | Mean-Delta² vorher | Mean-Delta² nachher |
|---|---:|---:|
| AC0712_1_L | 2492.811523 | 394.640900 |
| AC0712_1_M | 2682.712891 | 235.634293 |
| AC0712_1_S | 3822.055908 | 261.666656 |
| AC0712_L | 9471.785156 | 15.272000 |
| AC0712_M | 8555.514648 | 43.714287 |
| AC0712_S | 7349.221191 | 83.935997 |

**6/6 bestehen beide regulären Gates und die strengeren Pixelgrenzen, null
Pflichtmetrikregressionen.** Zwei unabhängige CLI-Abnahmen erzeugen identische
zwölf Vorher-/Nachher-SVGs und identische Gateberichte.
Verbotene Referenz-SVG-Zugriffe: null.

## Perception-Lerneffekt: generalisiert

Eine unabhängig konstruierte Vorlage mit anderer Geometrie, Farben und
Pixelphase besteht mit Seed `20261011` Original plus 16 Zufallsvarianten
über die echte CLI (**17/17**). Unabhängige Farbpolarität, Lage, Auflösung,
Umbenennung, fehlende Markierungen, falsche Strichrichtung, fehlender Griff,
zusätzliche Objekte, nicht endliche Daten und fehlendes Rendering sind geprüft.
Ein ausdrücklich beschriebener Text wird nicht als Strich-/Punktmotiv behandelt.

Der Nachweis erschließt diese Quadrat-/Griff-/Strich-/Punktstruktur;
beliebige andere Innenzeichen oder neue Topologien sind dadurch nicht belegt.
Die CLI-Restfehlerwarnungen bleiben sichtbar. Das historische Sammel-SVG
für das Ziel hatte `mean_delta2=12600.799805`; dieser alte Reviewwert wird
nicht mit der frischen Originalbeschreibung-Baseline verwechselt.

## Erfolgsübersicht und nächste Rotation

Die sechs Paare sind mit Beschreibung, Messwerten und Hashes separat in
`artifacts/satisfactory_conversions/` abgelegt. Die Übersicht enthält
**192** Paare; alle 186 älteren Indexeinträge bleiben unverändert.
Die frische erneute Konvertierung des gesamten Archivs besteht mit
**192/192 Review-Pässen**. Die 22 bekannten höheren Kompatibilitätsfehler
bleiben unverändert separat ausgewiesen. Der Bericht steht in
`artifacts/satisfactory_conversions/recheck_ac0712_2026-10-11.json`.
Die zehn schweren Bestandsschutz-, Conversion-Smoke- und Weak-Family-Tests
bestehen, einschließlich der 31 geschützten Varianten.

Der erneuerte Review enthält 1.000 Einträge mit 993 renderbaren Paaren;
alle 48 bisherigen Bestenlisteneinträge bleiben unter der unveränderten
Reviewgrenze. Nach Ausschluss der sechs erledigten Varianten folgt:
**`AC0734_1_S`**, `GE9021_1M`, `SE0081`, `GE0039_M`, `GE9022_2M`.
Bekannte Graufälle, ältere Archivdrift, U-Bogen-Stressprüfung und die
Katalogquellenprüfung bleiben separat offene Aufgaben.

Die fokussierte Quadrat-/Griff-/Textsuite besteht mit **100 Tests**.
Syntaxprüfung für `src`, `tests` und `tools`, CLI-Hilfe, Runtime-ID-Nullprüfung
und Diff-Prüfung mit Windows-Zeilenenden bestehen.
Der vollständige Standardtestlauf besteht mit **2.245 Tests, 30 bestehenden
Profil-/Windows-Skips und null Fehlern** in **2.656,80 Sekunden**.
Die drei unabhängigen Farb-/Lage-/Auflösungsfälle bestätigen zusätzlich die
abschließend dokumentierte Obergrenze von 1.442 Renderbewertungen.
Der kompakte Gesamtnachweis steht in
`artifacts/evaluation/left_stem_marked_square_recheck_v1/validation_2026-10-11.json`;
ausführliche lokale Logs unter `.tmp/ac0712-*.log`.

## Reproduktion

```powershell
$env:IMAGE_CONVERTER_ISOLATE_SVG_RENDER = '0'
.venv/Scripts/python.exe -m tools.run_top_stem_square_recheck artifacts/evaluation/left_stem_marked_square_recheck_v1/manifest.json --output-dir .tmp/left-square-reproduction
.venv/Scripts/python.exe -m tools.run_plan_b_variations --svg artifacts/evaluation/left_stem_marked_square_recheck_v1/independent.svg --description-file artifacts/evaluation/left_stem_marked_square_recheck_v1/independent.txt --seed 20261011 --output-dir .tmp/left-square-plan-b --keep-debug-artifacts
.venv/Scripts/python.exe -m tools.recheck_satisfactory_archive --output-dir .tmp/left-square-archive
$env:RUN_HEAVY_CONVERSION_TESTS = '0'
.venv/Scripts/python.exe -m pytest -q --basetemp .tmp/left-square-full
.venv/Scripts/python.exe -m compileall -q src tests tools
.venv/Scripts/python.exe -m src.imageCompositeConverter --help
.venv/Scripts/python.exe -m tools.check_no_new_image_id_hardcoding
```

Jeder Lauf benötigt ein frisches Ausgabeverzeichnis. Manifest, eingefrorene
Vorher-/Nachher-SVGs, Gatebericht, strenger Pixelbericht, unabhängige Vorlage,
CLI-Plan-B-Bericht, Reproduzierbarkeit und Review-Aufruf stehen unter
`artifacts/evaluation/left_stem_marked_square_recheck_v1/`.
