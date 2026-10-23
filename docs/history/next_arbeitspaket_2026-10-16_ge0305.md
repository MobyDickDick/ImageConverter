# Arbeitspaket – senkrechte Flaggenstreifen auf Verlaufsscheibe (2026-10-16)

Branch: `codex/ge0305-quality-2026-10-16`, Basis `69befdc5a`.
`GE0305` ist der nach GE1411 dokumentierte nächste reguläre Kandidat.
Das tatsächliche Flaggenbild besteht beide unveränderten regulären Gates
und die strengeren Plan-B-Pixelgrenzen ohne Pflichtmetrikregression.

## Quellen und allgemeiner Algorithmus

`GE0305.jpg` zeigt eine waagerechte rechteckige Flaggenfläche mit drei
senkrechten Streifen auf einer Kreisscheibe mit vertikalem Farbverlauf.
Die Streifen sind links grün, mittig hell und rechts rot. Beide XML-Kataloge
beschreiben diese Struktur nun eigenständig. Die drei Bilder
`GE0305_{L,M,S}` zeigen dagegen gekreuzte Werkzeuge und Tropfen. Sie sind
keine Flaggen-Holdouts. Ihre bisherigen Beschreibungen und Raster bleiben
unverändert; die Quellenzuordnung bleibt als `GE0305-TOOLS-SOURCE` offen.
Ursprüngliche Beschreibung, Hashes und Abmessungen aller vier Raster stehen
in `source_inventory.json`. Kein Quellraster wurde verändert.

Der bestehende Registrierer für drei waagerechte Streifen verarbeitet jetzt
auch senkrechte Streifen. Er bestimmt die Streifenrichtung ausdrücklich aus
der Beschreibung und verwirft widersprüchliche Richtungen. Ausschließlich
die Panelmessungen werden bei senkrechten Streifen transponiert. Kreis,
Canvas und vertikale Verlaufsachse bleiben im ursprünglichen Koordinatensystem.
Die gemeinsame Übergangssuche misst drei individuelle Breiten beziehungsweise
Höhen und Farben; die begrenzte Parametersuche prüft echte Produktionsrenderings.
Bei senkrechten JPEG-Farbkanten liegt die Uniformitätsprobe weiter im
Streifeninneren, damit Ringing nicht als zusätzliche Innenmarkierung gilt.
Die Fehler- und Qualitätsgrenzen bleiben unverändert; der tatsächlich
gerenderte Startkandidat bleibt eine harte Produktionsfehlerobergrenze.

Das SVG enthält einen weißen Hintergrund, einen Kreis mit nativem linearem
Farbverlauf und drei unmittelbar benachbarte gefüllte Rechtecke. Es enthält
keine Transformationsgruppen, Pixelkonturen oder Rastereinbettungen.
Die Runtime erhält ausschließlich Raster und Beschreibung und enthält keine
Bildkennungen, Katalogkoordinaten oder Referenz-SVGs. Für drei waagerechte
oder senkrechte einfarbige Streifen in einer vollständig im Kreis liegenden
waagerechten Rechteckfläche ist die Registrierung `generalisiert`.
Andere Streifenanzahlen, Zusatzzeichen und Werkzeugtopologien sind nicht
Bestandteil dieser Abnahme.

## Echte CLI-Abnahme und unabhängige Fälle

Die echte CLI-Baseline mit ursprünglicher Beschreibung und neutralem Dateinamen
wurde vor der Runtime-Änderung eingefroren. Vorher und Nachher verwenden
getrennte frische Wegwerfkopien. Die Wiederholung reproduziert das eingefrorene
Vorher-SVG bytegenau. Im vollständigen ursprünglichen und geänderten XML-Katalog
besteht der echte Dateiname seine eigene Vorher-/Nachher-Abnahme. Das finale
SVG ist bytegleich zur neutralen Ausgabe. Verbotene SVG-Lesezugriffe: null.
Alle Metriken stammen aus erneut gerenderten gespeicherten SVGs. Die getrennte
Semantikprüfung kontrolliert Richtung, lückenlose Verbindung, unterschiedliche
Füllungen, Kreiseinschluss und den weiterhin vertikalen Scheibenverlauf.

| Quelle | Mean-Delta² vorher (neutral) | Mean-Delta² nachher |
|---|---:|---:|
| GE0305.jpg | 9688.019531 | 246.678757 |

Die unabhängig konstruierte Vorlage verändert Zeichenfläche, Kreisposition,
Palette, Proportionen und Streifenbreiten. Zwei echte CLI-Läufe mit Seed
`20261016` bestehen jeweils **17/17** Fälle. Der Verifikator prüft
Eingangs-/Ausgangshashes, erneut gemessene Metriken, Gateentscheidungen und
die Gleichheit beider Läufe. 43 neue direkte Tests prüfen zusätzlich halbe
und doppelte Auflösung, andere Farben und Positionen, fehlende Streifen,
Lücken, falsche Richtungen, Zusatzpunkte, ungleiche Höhen, widersprüchliche
Beschreibungen und ungültige Eingaben oder Messungen. Die 42 bisherigen
Tests für waagerechte Streifen bestehen unverändert.

Die ersten Diagnosen unter `.tmp/vsr*` deckten JPEG-Ringing am Rand der
senkrechten Farbflächen auf. Sie bleiben erhalten und zählen nicht als
bestandene Abnahme. Die finale neutrale CLI-Abnahme liegt unter `.tmp/vsr3`.

## Bestandsschutz und nächste Rotation

Die Erfolgsübersicht enthält 306 Paare; alle 305 bisherigen Indexeinträge
bleiben unverändert. Die vollständige Standardsammlung besteht mit **3.072 bestandenen Tests, 30 bestehenden Skips und null Fehlern**.
Alle 3.102 gesammelten Testknoten sind genau einmal nachgewiesen.
Die erneute Archivkonvertierung besteht mit **306/306**; alle 305 bisherigen
Prüfdatensätze und die 22 bekannten älteren Kompatibilitätsabweichungen
bleiben unverändert. Die schweren AC08-/AC0100-Smoke-Tests bestehen mit **2/2**.
Abschlusszahlen und Artefakthashes stehen in
`artifacts/evaluation/vertical_striped_panel_disk_recheck_v1/validation_2026-10-16.json`.
Der erneuerte Review enthält unverändert 1.000 Einträge und 993 renderbare
Paare; alle 48 bisherigen Bestenlisteneinträge bleiben unter der unveränderten
Grenze. Ausschließlich das abgenommene Flaggenbild wird zusätzlich ausgeschlossen.
Die nächste reguläre Rotation lautet `GE9032_6M`, `AC0414_2_L`, `GE9033_6M`,
`AC0424_2_M`, `AC0840_S`. Bestehende offene Aufgaben bleiben erhalten.

## Reproduktion

CLI-Abnahmen benötigen frische Ausgabeverzeichnisse. Kurze Pfade vermeiden
die bereits dokumentierten Windows-I/O-Probleme langer Archivpfade.

```powershell
$env:IMAGE_CONVERTER_ISOLATE_SVG_RENDER = '0'
.venv/Scripts/python.exe artifacts/evaluation/vertical_striped_panel_disk_recheck_v1/verify_evidence.py
.venv/Scripts/python.exe -m tools.run_striped_panel_disk_recheck artifacts/evaluation/vertical_striped_panel_disk_recheck_v1/manifest.json --output-dir .tmp/v-reproduce
.venv/Scripts/python.exe artifacts/evaluation/vertical_striped_panel_disk_recheck_v1/recheck_catalog_context.py --output-dir .tmp/v-catalog
.venv/Scripts/python.exe -m tools.run_plan_b_variations --svg artifacts/evaluation/vertical_striped_panel_disk_recheck_v1/independent.svg --description-file artifacts/evaluation/vertical_striped_panel_disk_recheck_v1/independent.txt --seed 20261016 --output-dir .tmp/v-plan-b --keep-debug-artifacts
.venv/Scripts/python.exe artifacts/evaluation/labeled_disk_recheck_v1/recheck_archive_families.py --output-dir .tmp/v-archive
.venv/Scripts/python.exe artifacts/evaluation/spiral_disk_recheck_v1/run_standard_profile.py --output-dir .tmp/v-standard
$env:RUN_HEAVY_CONVERSION_TESTS = '1'
.venv/Scripts/python.exe -m pytest -q tests/test_vertical_striped_panel_disk_runtime.py tests/test_striped_panel_disk_runtime.py tests/test_conversion_regression_smoke.py --basetemp .tmp/v-focused
.venv/Scripts/python.exe -m compileall -q src tests tools
.venv/Scripts/python.exe -m src.imageCompositeConverter --help
.venv/Scripts/python.exe -m tools.check_no_new_image_id_hardcoding
git -c core.whitespace=cr-at-eol diff --check
```
