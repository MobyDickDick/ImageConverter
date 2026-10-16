# Arbeitspaket – T-Verzweigung mit Farbverlauf (2026-10-16)

Branch: `codex/ge9031-quality-2026-10-16`, Basis `c9998b34c`.
`GE9031_6M` ist der nach GE0001 dokumentierte nächste reguläre Kandidat.
Alle 14 Farb-/Größenvarianten bestehen beide unveränderten regulären Gates
und die strengeren Plan-B-Pixelgrenzen ohne Pflichtmetrikregression.

## Quelle und allgemeiner Algorithmus

Die Raster zeigen einen waagerechten Balken mit mittig nach oben anschließendem
senkrechtem Schaft. Beide Arme bilden eine verbundene T-Verzweigung. Quer zur
jeweiligen Längsrichtung liegt ein Farbverlauf mit heller Mitte und dunkleren
Rändern. Die gemeinsame Beschreibung „hellgraues Quadrat“ war unzutreffend.
Beide XML-Kataloge beschreiben die sichtbare Struktur nun eigenständig;
ursprüngliche Beschreibung, Rasterhashes und Abmessungen bleiben im
Quelleninventar erhalten. Die Rasterquellen bleiben unverändert.

Die Registrierung misst die T-Silhouette, die beiden rechteckigen Arme und
deren Farbprofile. Eine morphologische Schließung überbrückt helle Glanzlinien
bei der Topologieerkennung. Anschließend müssen die gemessenen Querprofile
entlang der Arme konsistent sein; Löcher und zusätzliche Elemente werden
verworfen. Regionale Farbmittel liefern einen groben Dreistopp-Startkandidaten.
Die detailliert gemessenen Profile sowie eine von Rand-Antialiasing bereinigte
Alternative werden getrennt verfeinert. Tatsächlich lineare Verläufe erhalten
drei analytische Stopps. Die begrenzte Parametersuche berücksichtigt Pixel,
Kanten und Vordergrundmasken; der Fehler des wirklich gerenderten Startkandidaten
unter der Produktionsmetrik bleibt eine harte Obergrenze.

Die SVG-Ausgabe enthält einen weißen Hintergrund, ein Rechteck und ein
fünfeckiges Schaftpolygon mit Gehrungsübergang sowie zwei native lineare
SVG-Verläufe. Sie enthält weder eingebettete Raster noch Pixelkonturen.
Die Runtime erhält ausschließlich Raster und Beschreibung und enthält keine
Bildkennungen, Referenz-SVGs oder gespeicherten Katalogparameter.
Für aufrechte T-Verzweigungen mit konsistenten querliegenden Glanzprofilen
ist die Registrierung `generalisiert`. Andere Verzweigungsrichtungen und
zusätzliche Innenzeichen gehören nicht zu dieser Abnahme.

## Echte CLI-Abnahme und unabhängige Fälle

Die neutral benannte CLI-Baseline mit ursprünglicher Beschreibung wurde vor
der Runtime-Änderung eingefroren. Vorher und Nachher erhalten getrennte frische
Wegwerfkopien. Der Reproduktionslauf reproduziert die eingefrorenen Baselines
bytegenau. Im vollständigen ursprünglichen und geänderten XML-Katalog bestehen
die echten Dateinamen ihre eigene Vorher-/Nachher-Abnahme; alle finalen SVGs
sind bytegleich zu den neutralen Ausgaben. Verbotene SVG-Lesezugriffe: null.
Die gespeicherten SVGs werden mit dem Produktionsrenderer erneut gemessen.
Eine getrennte Semantikprüfung kontrolliert T-Geometrie, Verbindung, native
Gradienten, Mittellinien und hellere Profilmitten.

| Quelle | Mean-Delta² vorher | Mean-Delta² nachher |
|---|---:|---:|
| GE9031_6M | 9455.181641 | 95.981873 |
| GE9031_1M | 7102.560059 | 203.117493 |
| GE9031_1S | 4976.692383 | 94.805000 |
| GE9031_2M | 6874.653320 | 181.582504 |
| GE9031_2S | 4717.722656 | 83.360001 |
| GE9031_3M | 4672.622559 | 147.888123 |
| GE9031_3S | 3309.830078 | 60.247501 |
| GE9031_4M | 2846.021973 | 70.435623 |
| GE9031_4S | 1126.117554 | 33.157501 |
| GE9031_5M | 5407.031250 | 59.883125 |
| GE9031_5S | 3958.814941 | 94.055000 |
| GE9031_6S | 6662.357422 | 105.157501 |
| GE9031_7M | 4728.131348 | 47.983124 |
| GE9031_7S | 3044.952393 | 64.129997 |

Die unabhängige violette Vorlage verändert Canvas, Lage, Proportionen und
Palette. Zwei echte CLI-Läufe mit Seed `20261016` bestehen jeweils alle **17/17**
Fälle (Original und 16 Zufallsvarianten). Die gespeicherten Belege und der Verifikator vergleichen
Eingangs-/Ausgangshashes, Metriken und Gateentscheidungen. Direkte Tests prüfen
zusätzlich halbe und doppelte Auflösung, andere Paletten, fehlende Arme,
zusätzliche Punkte, Löcher, flache Verläufe, widersprüchliche Texte und ungültige
Messungen. Auch direkte Tests verwenden die echte Produktionsfehlermetrik.

Die Diagnose deckte Rand-Antialiasing in den gemessenen Profilen und eine
Abweichung zwischen quadratischem Testfehler und absolutem Produktionsfehler
auf. Profilalternativen werden nun gegen denselben gerenderten Startkandidaten
geprüft. Bei kontrastarmen Profilen schützt eine zusätzliche Maskenbewertung
vor dem Verlust der Vordergrundfläche. Frühere Diagnoseläufe bleiben unter
`.tmp/junction-*` erhalten; die finalen Belege behaupten keine Abnahme dieser
früheren Läufe.

## Bestandsschutz und nächste Rotation

Die Erfolgsübersicht enthält 288 Paare. Alle 274 bisherigen Indexeinträge
bleiben unverändert. Die vollständige Standardsammlung besteht mit **2.944 bestandenen Tests.
30 bestehenden Skips und null Fehlern**. Alle 2.974 gesammelten
Testknoten sind genau einmal nachgewiesen. Beide schweren AC08-/AC0100-Smoke-Tests
bestehen. Die erneute Archivkonvertierung besteht mit **288/288**; alle 274
bisherigen Prüfdatensätze und die 22 bekannten älteren
Kompatibilitätsabweichungen bleiben unverändert. Abschlusszahlen und
Artefakthashes stehen in `validation_2026-10-16.json`.
Der Review enthält unverändert 1.000 Einträge und 993 renderbare Paare;
alle 48 bisherigen Bestenlisteneinträge bleiben unter der unveränderten Grenze.
Ausschließlich die 14 abgenommenen GE9031-Varianten werden zusätzlich
ausgeschlossen. Die nächste Rotation lautet `GE9034_6M`, `GE1411_L`, `GE0305`,
`GE9032_6M`, `AC0414_2_L`. Bestehende offene Folgeaufgaben bleiben erhalten.

## Reproduktion

Der erste Archivlauf besteht mit 240/240 semantischen Fällen, bricht aber beim
Schreiben von `conversion_bestlist.csv` im Kompatibilitätsteil mit Windows-
Fehler `OSError: [Errno 22] Invalid argument` ab. Nur die 48 betroffenen
Kompatibilitätsfälle werden in einem frischen kürzeren Ausgabepfad erneut
ausgeführt. Der Abschlussbericht führt die 240 ursprünglichen und 48 erneut
gemessenen Datensätze zusammen; der ursprüngliche Fehlerbericht und der
getrennte Wiederholungsbericht bleiben versioniert und werden verifiziert.

CLI-Prüfungen benötigen frische Ausgabeverzeichnisse.

```powershell
$env:IMAGE_CONVERTER_ISOLATE_SVG_RENDER = '0'
.venv/Scripts/python.exe artifacts/evaluation/gradient_junction_recheck_v1/verify_evidence.py
.venv/Scripts/python.exe -m tools.run_gradient_junction_recheck artifacts/evaluation/gradient_junction_recheck_v1/manifest.json --output-dir .tmp/junction-reproduce
.venv/Scripts/python.exe artifacts/evaluation/gradient_junction_recheck_v1/recheck_catalog_context.py --output-dir .tmp/junction-catalog-reproduce
.venv/Scripts/python.exe -m tools.run_plan_b_variations --svg artifacts/evaluation/gradient_junction_recheck_v1/independent.svg --description-file artifacts/evaluation/gradient_junction_recheck_v1/independent.txt --seed 20261016 --output-dir .tmp/junction-plan-b-reproduce --keep-debug-artifacts
.venv/Scripts/python.exe artifacts/evaluation/labeled_disk_recheck_v1/recheck_archive_families.py --output-dir .tmp/junction-archive-reproduce
.venv/Scripts/python.exe artifacts/evaluation/spiral_disk_recheck_v1/run_standard_profile.py --output-dir .tmp/junction-standard-reproduce
$env:RUN_HEAVY_CONVERSION_TESTS = '1'
.venv/Scripts/python.exe -m pytest -q tests/test_gradient_junction_runtime.py tests/test_conversion_regression_smoke.py --basetemp .tmp/junction-focused-reproduce
.venv/Scripts/python.exe -m compileall -q src tests tools
.venv/Scripts/python.exe -m src.imageCompositeConverter --help
.venv/Scripts/python.exe -m tools.check_no_new_image_id_hardcoding
git -c core.whitespace=cr-at-eol diff --check
```
