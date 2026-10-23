# Arbeitspaket – Kreis mit gerichteten Sehnen und Innen-T (2026-10-17)

Branch: `codex/ac0414-quality-2026-10-17`, Basis `3742bdf8c`.
`AC0414_2_L` ist der nach GE9032 dokumentierte nächste reguläre Kandidat.
Alle neun Farb-/Größen-/Richtungsvarianten bestehen beide unveränderten
regulären Gates ohne Pflichtmetrikregression. Die sechs farbigen JPGs bestehen
zusätzlich alle strengeren Plan-B-Pixelgrenzen. Der zusätzliche graue
IoU-Folgepunkt bleibt ausdrücklich offen.

## Quellen und allgemeiner Algorithmus

Die drei roten Raster zeigen einen gefüllten Kreis mit Kontur, zwei nach
unten konvergierenden Sehnen und einem inneren T mit Schaft nach unten.
Die drei grünen und drei grauen Raster zeigen dieselbe Topologie mit Schaft
nach links. Beide XML-Kataloge beschreiben diese Struktur jetzt eigenständig.
Die ursprünglichen Texte beider Kataloge, Rasterhashes und Abmessungen stehen
in `artifacts/evaluation/oriented_circle_linework_recheck_v1/source_inventory.json`.
Die Quellraster bleiben erhalten.

Die vorhandene Kreis-/Sehnen-/T-Registrierung wird um die vier beschriebenen
Hauptrichtungen erweitert. Sie normalisiert das Raster, bestimmt Kreis,
Füllung, Kontur und vier Linien aus den Pixeln und verfeinert die Parameter
durch begrenzte Suche. Jeder Suchkandidat wird im ursprünglichen Bildrahmen
gerendert und bewertet. Die Ausgabe dreht die nativen Kreis-/Linienkoordinaten
zurück; sie enthält weder Rastereinbettung noch SVG-Transformationen.
Ein zusätzlicher Zusammenhangstest für unerklärte Innenpixel verhindert,
dass ein einzelnes zusätzliches Zeichen im bisherigen prozentualen
Restpixelspielraum verschwindet. Bestehende ausreichende Vektoren bleiben
bytegleich. Die Runtime verwendet keine Bildkennungen, Katalogkoordinaten
oder Referenz-SVGs. Die Registrierung dieser Topologie ist `generalisiert`.

## CLI-Abnahme und unabhängige Fälle

Die neutrale CLI-Baseline mit ursprünglichen Beschreibungen wurde vor der
Runtime-Änderung eingefroren. Ein frischer Wiederholungslauf reproduziert
alle Baseline- und Ergebnis-SVGs bytegenau. Im vollständigen ursprünglichen
und geänderten Katalog bestehen die echten Dateinamen ihre eigene Abnahme;
die finalen SVGs sind bytegleich zur neutralen Ausgabe. Verbotene SVG-Lesezugriffe:
null. Der Verifikator rendert die gespeicherten Vektoren neu und prüft die
Semantik unabhängig über Kreis, vier Linien, Kreisrandanschlüsse und T-Richtung.

| Quelle | Mean-Delta² vorher | Mean-Delta² nachher |
|---|---:|---:|
| AC0414_2_L | 6908.101074 | 75.907501 |
| AC0414_1_L | 7982.025391 | 155.960632 |
| AC0414_1_M | 9107.812500 | 257.785553 |
| AC0414_1_S | 6306.492676 | 207.660004 |
| AC0414_2_M | 5915.026855 | 112.024445 |
| AC0414_2_S | 4984.975098 | 145.822495 |
| AC0414_L | 2302.469971 | 98.585625 |
| AC0414_M | 2016.703369 | 138.699997 |
| AC0414_S | 2735.092529 | 122.220001 |

Die unabhängig konstruierte violette Vorlage verändert Palette, Zeichenfläche,
Lage und Proportionen. Zwei CLI-Läufe mit Seed `20261017` bestehen jeweils
**17/17** Fälle. Ein weiterer Lauf nach dem Restpixel-Zusammenhangstest
reproduziert alle Ausgangshashes, Metriken und Entscheidungen.
47 neue direkte Tests prüfen die Katalogfamilie, unabhängige Farben,
halbe/doppelte Auflösung, Subpixelpositionen, alle vier Richtungen,
fehlende Linien, zusätzliche Punkte und widersprüchliche Beschreibungen.
Zusammen mit den 35 bestehenden Kreis-/T-Tests bestehen **82/82**.

Die grauen JPGs verfehlen ausschließlich die zusätzliche strengere
Vordergrund-IoU-Grenze `0.85`: L `0.748614`, M `0.718310`, S `0.821256`.
Die Füllung liegt bei ungefähr RGB 230 und damit am unveränderten
Vordergrundkriterium „mehr als 25 vom Hintergrund abweichend“.
JPEG-Abweichungen um diese Schwelle und ihre analytische Rekonstruktion
bleiben als `AC0414-PB-GREY` offen. Die reguläre Abnahme ist für alle neun
Varianten bestanden; das ist kein vollständiger strenger JPG-Nachweis.
Keine Grenze und kein Quellraster wurden verändert.

Frühere Diagnosen unter `.tmp/oclp1`, `.tmp/oclt*` und `.tmp/oclc`
bleiben erhalten und zählen nicht als erfolgreiche Abschlussläufe.
Die finale neutrale Wiederholung liegt unter `.tmp/ocl2`, der vollständige
Kataloglauf unter `.tmp/oclc2`, die unabhängigen CLI-Läufe unter
`.tmp/oclp2`, `.tmp/oclp3` und die finale Wiederholung unter `.tmp/oclp4`.

## Bestandsschutz und nächste Rotation

Die Erfolgsübersicht enthält 329 Paare. Alle 320 bisherigen Indexeinträge
bleiben unverändert. Die vollständige Standardsammlung besteht mit **3.164 bestandenen Tests, 30 bestehenden Skips und null Fehlern**.
Alle 3.194 gesammelten Testknoten sind genau einmal nachgewiesen.
Die erneute Archivkonvertierung besteht mit **329/329**; alle 320 bisherigen
Prüfdatensätze und die 22 bekannten älteren Kompatibilitätsabweichungen
bleiben unverändert. Die schweren AC08-/AC0100-Smoke-Tests bestehen mit **2/2**.
Vollständige Test- und Archivnachweise sind in
`artifacts/evaluation/oriented_circle_linework_recheck_v1/validation_2026-10-17.json`
versiegelt. Der Review enthält unverändert 1.000 Einträge und 993 renderbare
Paare; alle 48 bisherigen Bestenlisteneinträge bleiben unter derselben Grenze.
Nur die neun regulär abgenommenen AC0414-Varianten kommen als Ausschlüsse hinzu.
Die nächste Rotation lautet `GE9033_6M`, `AC0424_2_M`, `AC0840_S`,
`AC0840_M`, `SE0082`. Bestehende offene Aufgaben bleiben erhalten.

## Reproduktion

CLI-Abnahmen benötigen frische Ausgabeverzeichnisse; kurze Pfade vermeiden
die dokumentierten Windows-I/O-Probleme langer Archivpfade.

```powershell
$env:IMAGE_CONVERTER_ISOLATE_SVG_RENDER = '0'
.venv/Scripts/python.exe artifacts/evaluation/oriented_circle_linework_recheck_v1/verify_evidence.py
.venv/Scripts/python.exe -m tools.run_oriented_circle_linework_recheck artifacts/evaluation/oriented_circle_linework_recheck_v1/manifest.json --output-dir .tmp/oc-replay
.venv/Scripts/python.exe artifacts/evaluation/oriented_circle_linework_recheck_v1/recheck_catalog_context.py --output-dir .tmp/oc-catalog
.venv/Scripts/python.exe -m tools.run_plan_b_variations --svg artifacts/evaluation/oriented_circle_linework_recheck_v1/independent.svg --description-file artifacts/evaluation/oriented_circle_linework_recheck_v1/independent.txt --seed 20261017 --output-dir .tmp/oc-planb --keep-debug-artifacts
.venv/Scripts/python.exe artifacts/evaluation/labeled_disk_recheck_v1/recheck_archive_families.py --output-dir .tmp/oc-archive
.venv/Scripts/python.exe artifacts/evaluation/spiral_disk_recheck_v1/run_standard_profile.py --output-dir .tmp/oc-standard
$env:RUN_HEAVY_CONVERSION_TESTS = '1'
.venv/Scripts/python.exe -m pytest -q tests/test_circle_linework_runtime.py tests/test_oriented_circle_linework_runtime.py tests/test_conversion_regression_smoke.py --basetemp .tmp/oc-focused
.venv/Scripts/python.exe -m compileall -q src tests tools
.venv/Scripts/python.exe -m src.imageCompositeConverter --help
.venv/Scripts/python.exe -m tools.check_no_new_image_id_hardcoding
git -c core.whitespace=cr-at-eol diff --check
```
