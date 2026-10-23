# Arbeitspaket – Kreuz auf Rechteckfläche vor Verlaufsscheibe (2026-10-14)

Branch: `codex/ge0300-quality-2026-10-14`, Basis `74c5c21f7`.
`GE0300` ist der nach GE9024 dokumentierte nächste reguläre Kandidat.
Das gespeicherte finale SVG besteht beide unveränderten regulären Gates und
die strengeren Plan-B-Pixelgrenzen ohne Pflichtmetrikregression.

## Quellenprüfung und allgemeine Registrierung

Der Katalogeintrag enthält genau ein Bild. Die bisherige Beschreibung verweist
auf eine andere Hintergrundkennung und nennt eine falsch proportionierte
Schweizerfahne. Das Raster zeigt eine Kreisscheibe mit heller Randkontur und
vertikalem Verlauf, eine waagerechte rote Rechteckfläche und ein helles
rechtwinkliges Kreuz mit vier freien Armen. Die Proportionen des Rasters sind
für die Konvertierung maßgebend. Beide XML-Kataloge enthalten jetzt dieselbe
eigenständige Beschreibung dieser Primitive und ihrer Einschlussbeziehungen.
Das Quelleninventar hält den unveränderten Bildhash und die Abmessungen fest.

Die neue allgemeine Registrierung ermittelt Kreis, Farbverlauf, Rechteck und
Kreuz aus dem Raster. Die äußere Kreisgrenze und freie Bereiche oberhalb und
unterhalb des Rechtecks liefern den Startkandidaten für die Verlaufsscheibe.
Farbkontrast, zusammenhängende Komponenten und breite mittlere Zeilen-/
Spaltenabschnitte erkennen die Rechteckfläche und das rechtwinklige Kreuz.
Eine begrenzte iterative Pixelsuche verfeinert Geometrie, Farben und Konturen;
der Ausgangsfehler bleibt eine harte Obergrenze. Fehlende Primitive, diagonale
oder unterbrochene Kreuze, zusätzliche Objekte und widersprüchliche
Beschreibungen werden durch eigene Negativtests geprüft.

Die Ausgabe besteht aus Hintergrundrechteck, Kreis mit nativem SVG-Verlauf,
Rechteckfläche und analytischem Kreuzpolygon. Die Rasterkontur dient nur zur
Messung. Es werden keine Katalogkennungen oder Referenzvektoren in der Runtime
verwendet. Die Registrierung ist für die geprüften Farb-, Geometrie-, Lage-
und Auflösungsfälle `generalisiert`; weitere Symboltopologien bleiben eigene
Arbeitspakete.

## CLI-Abnahme und unabhängige Fälle

Der tatsächliche CLI-Vorlauf mit Originalbeschreibung wurde vor der Runtime-
und XML-Änderung erzeugt und eingefroren. Frische Wegwerfkopien isolieren beide
Seiten. Der Runner prüft den Quellhash, sperrt fremde SVG-Zugriffe und vergleicht
gespeicherte Vorher-/Nachher-SVGs bei Wiederholung bytegenau. Bewertet wird das
auf Platte gespeicherte SVG nach erneutem Rendern mit dem Produktionsrenderer.
Mean-Delta² sinkt von **10814.927734 auf 284.043915**. Beide regulären Gates,
die unabhängige Kreis-/Rechteck-/Kreuz-Semantik und alle strengeren Pixelgrenzen
bestehen. Die Pflichtmetriken zeigen keine Regression; fremde Referenz-SVG-
Zugriffe treten nicht auf.

Die separate Katalogabnahme verwendet den echten Bildnamen und den vollständigen
Originalkatalog aus dem Basiscommit. Ihr Vorlauf und der neutrale Vorlauf sind
bytegleich; ihr finales SVG ist ebenfalls bytegleich mit der neutralen Ausgabe.
Die ursprünglichen und finalen Vektoren sowie die getrennten Gateberichte
bleiben im Paket erhalten.

Eine unabhängig konstruierte Vorlage verändert Canvas, Größenverhältnisse,
relative Lage und Palette: grüner Kreis, violette Fläche und cremefarbenes Kreuz.
Die echte CLI prüft Original und 16 Zufallsvarianten mit Seed `20261014` zweimal
mit **17/17** bestandenen Fällen. Eingangs-/Ausgangshashes, Metriken, Komplexität
und Gateentscheidungen sind identisch. Direkte Rastertests prüfen zusätzlich
halbe und doppelte Auflösung, Verschiebung, andere Farben, fehlende oder
zusätzliche Primitive, widersprüchliche Texte und ungültige Messungen.

Die erste unabhängige CLI-Diagnose bestand 12/17 Fälle. Subpixel-Antialiasing
verkürzte die Kreuzarme an einzelnen Randpixeln; außerdem erzeugten gemischte
Kantenfarben kleine Löcher in der Kontrastmaske der umgebenden Rechteckfläche.
Die Erkennung berücksichtigt diese Effekte über die beobachtete äußere
Silhouette und breite mittlere Abschnitte. Alle Qualitätsgrenzen bleiben
unverändert. Diese Diagnose zählt nicht als finale Abnahme.

## Bestandsschutz und nächste Rotation

Die Erfolgsübersicht enthält **252 Paare**. Alle 251 bisherigen Indexeinträge
bleiben identisch. Die vollständige Prüfung in getrennten Familienprozessen
besteht mit **252/252**. Alle 251 bisherigen erneut gemessenen Mean-Delta²-Werte
und die 22 bekannten älteren Kompatibilitätsabweichungen bleiben unverändert.
Die fokussierte Suite besteht mit **43 Tests**, die AC08-/AC0100-Smoke-Prüfung
mit zwei Tests. Der vollständige Standardlauf besteht mit **2.630 Tests und
30 bestehenden Skips, null Fehlern**. Syntaxprüfung, CLI-Hilfe, Runtime-ID-
Nullprüfung, Artefakthashes und Diff-Prüfung bestehen.
Die finalen Test- und Archivzahlen sowie die Wiederholungs-
und Hashnachweise stehen in
`artifacts/evaluation/cross_panel_disk_recheck_v1/validation_2026-10-14.json`.

Der erneuerte Review umfasst 1.000 Einträge und 993 renderbare Paare. Alle
48 bisherigen Bestenlisteneinträge bleiben unter der unveränderten Grenze.
Bisherige Ausschlüsse werden fortgeschrieben; das abgenommene GE0300-Bild ist
zusätzlich ausgeschlossen. Es folgen **`b_heating1`**, `AC0421_1_S`, `GE0306`,
`GE0346` und `AC0850_L`. Bestehende offene Aufgaben einschließlich des getrennten
Glocken-Quellenpunkts GE0022-BELL-SOURCE bleiben erhalten.

```powershell
$env:IMAGE_CONVERTER_ISOLATE_SVG_RENDER = '0'
.venv/Scripts/python.exe -m tools.run_cross_panel_disk_recheck artifacts/evaluation/cross_panel_disk_recheck_v1/manifest.json --output-dir .tmp/cross-panel-reproduce
.venv/Scripts/python.exe artifacts/evaluation/cross_panel_disk_recheck_v1/recheck_catalog_context.py --output-dir .tmp/cross-panel-catalog-reproduce
.venv/Scripts/python.exe -m tools.run_plan_b_variations --svg artifacts/evaluation/cross_panel_disk_recheck_v1/independent.svg --description-file artifacts/evaluation/cross_panel_disk_recheck_v1/independent.txt --seed 20261014 --output-dir .tmp/cross-panel-plan-b-reproduce --keep-debug-artifacts
.venv/Scripts/python.exe artifacts/evaluation/labeled_disk_recheck_v1/recheck_archive_families.py --output-dir .tmp/cross-panel-archive-reproduce
$env:RUN_HEAVY_CONVERSION_TESTS = '0'
.venv/Scripts/python.exe -m pytest -q --basetemp .tmp/cross-panel-tests-reproduce
$env:RUN_HEAVY_CONVERSION_TESTS = '1'
.venv/Scripts/python.exe -m pytest -q tests/test_conversion_regression_smoke.py --basetemp .tmp/cross-panel-smoke-reproduce
.venv/Scripts/python.exe -m compileall -q src tests tools
.venv/Scripts/python.exe -m src.imageCompositeConverter --help
.venv/Scripts/python.exe -m tools.check_no_new_image_id_hardcoding
git -c core.whitespace=cr-at-eol diff --check
```

CLI-Prüfungen benötigen frische Ausgabeverzeichnisse. Das Paket versioniert
Manifest, echte Baselines, finale Vektoren, Quelleninventar, Gateberichte,
unabhängige Vorlage und die Belege beider Plan-B-Läufe. Vollständige
Diagnoseläufe bleiben lokal unter `.tmp/cross-panel-*` erhalten.
