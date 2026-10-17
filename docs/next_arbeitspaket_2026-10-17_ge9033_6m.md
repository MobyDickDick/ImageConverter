# Arbeitspaket – T-Verzweigung mit Schaft nach unten (2026-10-17)

Branch: `codex/ge9033-quality-2026-10-17`, Basis `a830dc53d`.
`GE9033_6M` war nach AC0414 der nächste dokumentierte reguläre Kandidat.
Alle 14 Farb-/Größenvarianten bestehen beide unveränderten regulären
Qualitätsgates ohne Pflichtmetrikregression. 13 bestehen zusätzlich die
strengeren Plan-B-Pixelgrenzen; ein eigener Folgepunkt bleibt offen.

## Ursache und Änderung

Die Raster zeigen eine T-Verzweigung: waagerechter Balken oben, mittig nach
unten anschließender senkrechter Schaft, beide mit querliegenden Farbverläufen
und heller Mitte. Die Beschreibung „Wie BackBottom: hellgraues Quadrat“
war unzutreffend. Beide XML-Kataloge beschreiben jetzt eigenständig diese
T-Struktur. Ursprüngliche Texte, Rasterhashes und Maße bleiben unter
`artifacts/evaluation/down_gradient_junction_recheck_v1/source_inventory.json`
erhalten. Die Quellraster wurden nicht verändert.

Die bestehende allgemeine Richtungsnormalisierung und Rasterregistrierung
unterstützt diese Topologie bereits. Dieses Paket verändert keinen Runtime-Code.
Geometrie und Farbverläufe werden weiterhin aus Raster und Beschreibung bestimmt;
der Konverter erhält keine Bildkennungen, Katalogmaße oder Referenz-SVGs.

## Vorher-/Nachher-Abnahme

Echte CLI-Läufe mit neutralen Dateinamen verwenden getrennte Wegwerfkopien
und die ursprüngliche bzw. korrigierte Beschreibung. Der Prüfer rendert die
gespeicherten SVGs neu und kontrolliert T-Geometrie, Verbindung, Gehrung und
Gradienten unabhängig. Verbotene SVG-Lesezugriffe: null.
Im vollständigen ursprünglichen und korrigierten XML-Katalog bestehen die
echten Dateinamen dieselbe reguläre Abnahme; ihre finalen SVGs sind bytegleich
zur neutralen Ausgabe. Die ursprüngliche Quadratbeschreibung aktiviert die
T-Registrierung nicht.

| Quelle | Mean-Delta² vorher | Mean-Delta² nachher |
|---|---:|---:|
| GE9033_6M | 9455.181641 | 102.153122 |
| GE9033_1M | 7163.095215 | 114.318748 |
| GE9033_1S | 4651.207520 | 86.275002 |
| GE9033_2M | 6797.306152 | 120.201248 |
| GE9033_2S | 4766.502441 | 77.232498 |
| GE9033_3M | 4648.533691 | 87.933128 |
| GE9033_3S | 2214.457520 | 61.060001 |
| GE9033_4M | 2835.294922 | 32.671249 |
| GE9033_4S | 1110.869995 | 45.062500 |
| GE9033_5M | 5408.891113 | 50.720627 |
| GE9033_5S | 4020.652588 | 66.605003 |
| GE9033_6S | 6714.419922 | 106.862503 |
| GE9033_7M | 4728.000000 | 40.880001 |
| GE9033_7S | 3131.824951 | 65.834999 |

Die unabhängig konstruierte blaugrüne Vorlage verändert Zeichenfläche, Lage,
Proportionen und Palette. Zwei echte CLI-Läufe bestehen jeweils **17/17** Fälle (Original plus 16
Zufallsvarianten) mit Seed `20261017` und reproduzieren dieselben Hashes und Metriken. Die direkten Tests umfassen alle 14
Katalogbilder, 16 unabhängige Variationen, andere Farben und Auflösungen,
widersprüchliche Beschreibungen, fehlende Arme, Zusatzpunkte, Löcher und
flache Verläufe sowie beide XML-Kataloge und die gespeicherte CLI-Abnahme.

`GE9033_4M` verfehlt ausschließlich die zusätzliche strengere Vordergrund-IoU:
**0.8490196078431372 < 0.85**. Reguläre Abnahme und alle anderen strengen
Metriken bestehen. Die sehr helle graue Fläche liegt nahe der unveränderten
Vordergrundschwelle von mehr als 25 Abstand zum Hintergrund. Dieser Fall
bleibt als `GE9033-PB-GREY` offen; keine Grenze wurde abgesenkt. Die Tests
halten den Befund ausdrücklich fest und zählen ihn nicht als strengen Pass.
Der gemeinsame Recheck-Runner liefert deshalb Exitcode 2 trotz 14/14
regulärer Abnahmen. Der katalogbezogene Prüfer kontrolliert den einen
erwarteten strengen Fehler explizit.

## Bestandsschutz und nächste Rotation

Die Erfolgsübersicht enthält 343 Paare. Alle 329 bisherigen Indexeinträge
bleiben unverändert. Die vollständige Standardsammlung besteht mit **3.209 bestandenen Tests, 30 bestehenden Skips und null Fehlern**. Alle 3.239 Testknoten sind genau einmal nachgewiesen.
Die erneute Archivkonvertierung besteht mit **343/343**; alle 329 bisherigen
Prüfdatensätze und die 22 bekannten älteren Kompatibilitätsabweichungen
bleiben unverändert. Die schweren AC08-/AC0100-Smoke-Tests bestehen mit **2/2**.
Vollständige Test- und Archivnachweise sind in
`artifacts/evaluation/down_gradient_junction_recheck_v1/validation_2026-10-17.json`
versiegelt. Der Review behält seine 1.000 Datensätze und 993 renderbaren Paare;
alle 48 bisherigen Bestenlisteneinträge bleiben unter derselben Grenze.
Nur die 14 regulär abgenommenen GE9033-Varianten kommen als Ausschlüsse hinzu.
Die nächste Rotation lautet `AC0424_2_M`, `AC0840_S`, `AC0840_M`, `SE0082`,
`AC0411_1_M`. Bestehende offene Aufgaben bleiben erhalten.

Die [aktuelle Bestandsaufnahme](project_status_2026-10-17.md) unterscheidet
ausdrückliche Abnahme, ältere Pixelprüfung und noch fehlenden Nachweis.
Eine sortierte CSV-Prüfliste erleichtert die persönliche Sichtprüfung für Samples.

## Reproduktion

Frische Ausgabeverzeichnisse und kurze Windows-Pfade verwenden.

```powershell
$env:IMAGE_CONVERTER_ISOLATE_SVG_RENDER = '0'
.venv/Scripts/python.exe artifacts/evaluation/down_gradient_junction_recheck_v1/verify_evidence.py
# Exit 2 erwartet: regulär 14/14, streng 13/14 (GE9033_4M bleibt offen).
.venv/Scripts/python.exe -m tools.run_gradient_junction_recheck artifacts/evaluation/down_gradient_junction_recheck_v1/manifest.json --output-dir .tmp/dj-replay
.venv/Scripts/python.exe artifacts/evaluation/down_gradient_junction_recheck_v1/recheck_catalog_context.py --output-dir .tmp/dj-catalog
.venv/Scripts/python.exe -m tools.run_plan_b_variations --svg artifacts/evaluation/down_gradient_junction_recheck_v1/independent.svg --description-file artifacts/evaluation/down_gradient_junction_recheck_v1/independent.txt --seed 20261017 --output-dir .tmp/dj-planb --keep-debug-artifacts
.venv/Scripts/python.exe artifacts/evaluation/labeled_disk_recheck_v1/recheck_archive_families.py --output-dir .tmp/dj-archive
.venv/Scripts/python.exe artifacts/evaluation/spiral_disk_recheck_v1/run_standard_profile.py --output-dir .tmp/dj-standard
$env:RUN_HEAVY_CONVERSION_TESTS = '1'
.venv/Scripts/python.exe -m pytest -q tests/test_conversion_regression_smoke.py --basetemp .tmp/dj-smoke
.venv/Scripts/python.exe artifacts/evaluation/conversion_status_2026-10-17/generate_snapshot.py
.venv/Scripts/python.exe -m compileall -q src tests tools
.venv/Scripts/python.exe -m src.imageCompositeConverter --help
.venv/Scripts/python.exe -m tools.check_no_new_image_id_hardcoding
git -c core.whitespace=cr-at-eol diff --check
```
