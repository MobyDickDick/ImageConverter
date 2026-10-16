# Arbeitspaket – seitliche T-Verzweigung mit Farbverlauf (2026-10-16)

Branch: `codex/ge9034-quality-2026-10-16`, Basis `3297925e2`.
`GE9034_6M` ist der nach GE9031 dokumentierte nächste reguläre Kandidat.
Alle 14 Farb-/Größenvarianten bestehen beide unveränderten regulären Gates
und die strengeren Plan-B-Pixelgrenzen ohne Pflichtmetrikregression.

## Quellen und allgemeiner Algorithmus

Die Raster zeigen einen senkrechten Balken mit mittig nach links anschließendem
waagerechtem Schaft. Beide Arme sind verbunden und haben quer zu ihrer
Längsrichtung einen Farbverlauf mit heller Mitte und dunkleren Rändern.
Die gemeinsame Beschreibung „hellgraues Quadrat“ war falsch. Beide XML-Kataloge
beschreiben nun eigenständig diese T-Struktur. Ursprüngliche Beschreibung,
Quellhashes und Abmessungen stehen in `source_inventory.json`; die Raster bleiben
unverändert.

Der bestehende allgemeine T-Registrierer normalisiert die beschriebene
Schaftrichtung durch eine verlustfreie Vierteldrehung des Eingangsrasters.
Er misst danach dieselben rechteckigen Arme, Profile und Gehrungsübergänge
wie bisher. Für jeden Suchschritt werden Vektorkoordinaten und native
Gradientenachsen in die ursprüngliche Bildrichtung zurückgeführt und dort mit
dem Produktionsrenderer gerendert. Auch die harte Fehlerobergrenze des
Startkandidaten verwendet die tatsächliche Produktionsmetrik in der
ursprünglichen Bildrichtung. Die Ausgabe enthält einen weißen Hintergrund,
ein Rechteck, ein fünfeckiges Polygon und zwei native lineare SVG-Verläufe.
Sie benötigt weder Transformationsgruppen noch Rastereinbettungen oder
Pixelkonturen.

Richtungsangaben zur Verschiebung des gesamten Motivs werden getrennt von
der Schaftrichtung gelesen. Der erste Diagnoselauf verwechselte diese Angaben
und scheiterte bei Zufallsvarianten. Die Korrektur wird durch dieselben
unabhängigen Verschiebungen geprüft; widersprüchliche Schaftrichtungen bleiben
Ablehnungsfälle. Die Diagnosen bleiben unter `.tmp/side-pb*` und
`.tmp/side-focused*` erhalten und zählen nicht als bestandene Abnahme.

Die Runtime erhält ausschließlich Raster und Beschreibung. Sie enthält keine
Bildkennungen, gespeicherten Katalogmaße oder Referenz-SVGs. Die
Richtungsnormalisierung ist für T-Verzweigungen in allen vier Hauptrichtungen
`generalisiert`; direkte Tests prüfen jede Richtung auf rechteckiger
Zeichenfläche. Andere Topologien und zusätzliche Innenzeichen bleiben außerhalb
dieser Abnahme.

## Echte CLI-Abnahme und unabhängige Fälle

Vor der Runtime-Änderung wurde eine echte CLI-Baseline mit der ursprünglichen
Beschreibung und neutralen Dateinamen eingefroren. Vorher und Nachher erhalten
jeweils frische Wegwerfkopien. Der anschließende Abnahmelauf reproduziert alle
eingefrorenen Vorher-SVGs bytegenau. Im vollständigen ursprünglichen und
geänderten XML-Katalog bestehen die echten Dateinamen ihre eigene
Vorher-/Nachher-Abnahme; alle finalen SVGs sind bytegleich zu den neutralen
Ausgaben. Verbotene SVG-Lesezugriffe: null. Gespeicherte SVGs werden mit dem
Produktionsrenderer erneut vermessen. Eine getrennte richtungsabhängige
Semantikprüfung kontrolliert T-Geometrie, Verbindung, Gehrung und Gradienten.

| Quelle | Mean-Delta² vorher | Mean-Delta² nachher |
|---|---:|---:|
| GE9034_6M | 9454.780273 | 83.588753 |
| GE9034_1M | 7106.374512 | 196.654373 |
| GE9034_1S | 4977.567383 | 99.212502 |
| GE9034_2M | 6846.569336 | 165.306870 |
| GE9034_2S | 3524.732422 | 81.502502 |
| GE9034_3M | 4676.350098 | 146.765625 |
| GE9034_3S | 2136.097412 | 63.619999 |
| GE9034_4M | 1827.572510 | 62.508125 |
| GE9034_4S | 1406.079956 | 29.542500 |
| GE9034_5M | 6739.257324 | 51.854374 |
| GE9034_5S | 3915.297607 | 76.489998 |
| GE9034_6S | 4533.397461 | 103.754997 |
| GE9034_7M | 4735.475586 | 41.880001 |
| GE9034_7S | 3043.752441 | 67.489998 |

Die unabhängig konstruierte grüne Vorlage verändert Zeichenfläche, Lage,
Proportionen und Palette. Zwei echte CLI-Läufe mit Seed `20261016` bestehen
jeweils **17/17** Fälle. Der Verifikator prüft Eingangs-/Ausgangshashes,
gespeicherte Metriken und Gateentscheidungen sowie die Gleichheit beider Läufe.
Direkte Tests prüfen zusätzlich andere Farben, halbe und doppelte Auflösung,
alle vier Richtungen, fehlende Arme, zusätzliche Punkte, Löcher, flache Verläufe,
widersprüchliche Beschreibungen sowie ungültige Render- und Fehlerwerte.

## Bestandsschutz und nächste Rotation

Die Erfolgsübersicht enthält 302 Paare. Alle 288 bisherigen Indexeinträge
bleiben unverändert. Die vollständige Standardsammlung besteht mit **2.993
bestandenen Tests, 30 bestehenden Skips und null Fehlern**. Alle 3.023
gesammelten Testknoten sind genau einmal nachgewiesen. Die erneute
Archivkonvertierung besteht mit **302/302**; alle 288 bisherigen Prüfdatensätze
und die 22 bekannten älteren Kompatibilitätsabweichungen bleiben unverändert.
Abschlusszahlen und Artefakthashes stehen in
`artifacts/evaluation/side_gradient_junction_recheck_v1/validation_2026-10-16.json`. Die schweren AC08-/AC0100-Smoke-Tests bestehen mit **2/2**.
Der Review enthält unverändert 1.000 Einträge und 993 renderbare Paare;
alle 48 bisherigen Bestenlisteneinträge bleiben unter der unveränderten Grenze.
Ausschließlich die 14 abgenommenen GE9034-Varianten werden zusätzlich
ausgeschlossen. Die nächste reguläre Rotation lautet `GE1411_L`, `GE0305`,
`GE9032_6M`, `AC0414_2_L`, `GE9033_6M`. Bestehende offene Aufgaben bleiben erhalten.

## Reproduktion

CLI-Abnahmen benötigen frische Ausgabeverzeichnisse. Kurze Pfade vermeiden
die bereits dokumentierten Windows-I/O-Probleme langer Archivpfade.

```powershell
$env:IMAGE_CONVERTER_ISOLATE_SVG_RENDER = '0'
.venv/Scripts/python.exe artifacts/evaluation/side_gradient_junction_recheck_v1/verify_evidence.py
.venv/Scripts/python.exe -m tools.run_gradient_junction_recheck artifacts/evaluation/side_gradient_junction_recheck_v1/manifest.json --output-dir .tmp/sdr
.venv/Scripts/python.exe artifacts/evaluation/side_gradient_junction_recheck_v1/recheck_catalog_context.py --output-dir .tmp/sdc
.venv/Scripts/python.exe -m tools.run_plan_b_variations --svg artifacts/evaluation/side_gradient_junction_recheck_v1/independent.svg --description-file artifacts/evaluation/side_gradient_junction_recheck_v1/independent.txt --seed 20261016 --output-dir .tmp/sdp --keep-debug-artifacts
.venv/Scripts/python.exe artifacts/evaluation/labeled_disk_recheck_v1/recheck_archive_families.py --output-dir .tmp/sdar
.venv/Scripts/python.exe artifacts/evaluation/spiral_disk_recheck_v1/run_standard_profile.py --output-dir .tmp/sds
$env:RUN_HEAVY_CONVERSION_TESTS = '1'
.venv/Scripts/python.exe -m pytest -q tests/test_side_gradient_junction_runtime.py tests/test_gradient_junction_runtime.py tests/test_conversion_regression_smoke.py --basetemp .tmp/sdf
.venv/Scripts/python.exe -m compileall -q src tests tools
.venv/Scripts/python.exe -m src.imageCompositeConverter --help
.venv/Scripts/python.exe -m tools.check_no_new_image_id_hardcoding
git -c core.whitespace=cr-at-eol diff --check
```
