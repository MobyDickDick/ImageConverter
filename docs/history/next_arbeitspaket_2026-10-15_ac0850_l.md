# Arbeitspaket – Kreisscheibe mit P (2026-10-15)

Branch: `codex/ac0850-quality-2026-10-15`, Basis `ef74f0ed8`.
`AC0850_L` ist der nach GE0346 dokumentierte nächste reguläre Kandidat.
Alle drei Größen bestehen beide unveränderten regulären Gates und die
strengeren Plan-B-Pixelgrenzen ohne Pflichtmetrikregression.

## Ursache und Korrektur

Die Raster `AC0850_{L,M,S}` zeigen eine hellgrau gefüllte Kreisscheibe mit
dunkler Kontur und einem dunklen serifenlosen P. Beide Kataloge beschrieben
stattdessen rF. Die eigenständige Beschreibung benennt jetzt die sichtbaren
Primitive, den Großbuchstaben P und den fehlenden Anschluss. Ursprüngliche
Beschreibung, Rasterhashes und Abmessungen bleiben im Quelleninventar erhalten.
Die Rasterdateien bleiben unverändert.

Die vorhandene allgemeine Kreis-/Textregistrierung regressiert Kreis und
Farben aus dem Raster, gleicht den beschriebenen nativen Schriftzug mit dem
Bildsignal ab und verfeinert die Parameter durch begrenzte Pixelsuche.
Der Runtime-Code bleibt unverändert. Er speichert weder Kennungen noch
Bildparameter und liest keine Referenz-SVGs. Die Ausgabe enthält genau ein
Hintergrundrechteck, einen Kreis und nativen SVG-Text. Der bereits abgenommene
allgemeine Algorithmus reicht für diese Quellen aus.

## Abnahme

Die echte CLI-Baseline mit ursprünglicher Beschreibung und neutralen Dateinamen
wurde vor der Katalogänderung eingefroren. Jede Vorher-/Nachher-Seite erhält
frische Wegwerfkopien. Quellhashes und fremde SVG-Lesezugriffe werden geprüft.
Zwei neutrale Läufe reproduzieren alle sechs SVGs und Gateentscheidungen.
Zwei Läufe mit vollständigem ursprünglichem beziehungsweise geändertem Katalog
reproduzieren ihre eigenständig eingefrorene Baseline. Alle drei finalen
Katalog-SVGs sind bytegleich mit den neutralen Ausgaben.

| Quelle | Mean-Delta² vorher | Mean-Delta² nachher |
|---|---:|---:|
| AC0850_L | 7792.040039 | 347.363342 |
| AC0850_M | 5271.097656 | 248.467499 |
| AC0850_S | 8481.933594 | 450.813324 |

Bewertet werden die gespeicherten SVGs nach erneutem Rendern mit dem
Produktionsrenderer. Es gibt null Pflichtmetrikregressionen und null fremde
Referenz-SVG-Zugriffe. Die unabhängige Semantikprüfung verlangt einen
vollständig sichtbaren gefüllten Kreis mit dunkler Kontur und genau den
nativen Text P.

Eine unabhängig konstruierte violette Kreisscheibe verändert Canvas,
Kreisposition, Radius, Strichstärke, Schriftgröße und Palette. Zwei echte
CLI-Läufe mit Seed `20261015` bestehen jeweils **17/17**. Eingangs-/Ausgangshashes,
Metriken, Komplexität und Gateentscheidungen sind identisch. Die gespeicherten
Referenzen werden ausschließlich von der Abnahme rasterisiert; der Konverter
bekommt nur Raster und Beschreibung.

Die fokussierte Batterie besteht mit **47 Tests**, einschließlich der bisherigen
unabhängigen Buchstaben-, Geometrie-, Negativ- und Abgrenzungsfälle sowie zwei
schweren AC08-/AC0100-Smoke-Tests. Drei neue Regressionen prüfen die tatsächlich
geladenen Beschreibungen beider Kataloge und die Pixel-/P-Semantik jeder Größe.

## Bestandsschutz und nächste Rotation

Die Erfolgsübersicht enthält **267 Paare**. Alle 264 bisherigen Indexeinträge
bleiben unverändert. Der frische Review umfasst 1.000 Einträge und 993
renderbare Paare; alle 48 bisherigen Bestenlisteneinträge bleiben unter der
unveränderten Grenze. Bestehende Ausschlüsse bleiben erhalten. Zusätzlich
werden ausschließlich die drei abgenommenen AC0850-Größen ausgeschlossen.
Es folgen **`GE0017`**, `GE0001_L`, `GE9031_6M`, `GE9034_6M` und `GE1411_L`.
Die bisherigen offenen Folgeaufgaben bleiben erhalten.

Die vollständige Standardsammlung besteht mit **2.808 bestandenen Tests,
30 bestehenden Skips und null Fehlern**. Alle 2.838 gesammelten Testknoten
wurden genau einmal ausgeführt. Die getrennte Archivkonvertierung besteht
mit **267/267**; alle 264 bisherigen Prüfdatensätze und die 22 bekannten
älteren Kompatibilitätsabweichungen bleiben unverändert.

## Reproduktion

Die Abschlusszahlen und Artefakthashes stehen unter
`artifacts/evaluation/p_letter_disk_recheck_v1/validation_2026-10-15.json`.
CLI-Prüfungen benötigen frische Ausgabeverzeichnisse.

```powershell
$env:IMAGE_CONVERTER_ISOLATE_SVG_RENDER = '0'
.venv/Scripts/python.exe artifacts/evaluation/p_letter_disk_recheck_v1/verify_evidence.py
.venv/Scripts/python.exe -m tools.run_labeled_disk_recheck artifacts/evaluation/p_letter_disk_recheck_v1/manifest.json --output-dir .tmp/p-letter-reproduce
.venv/Scripts/python.exe artifacts/evaluation/p_letter_disk_recheck_v1/recheck_catalog_context.py --output-dir .tmp/p-letter-catalog-reproduce
.venv/Scripts/python.exe -m tools.run_plan_b_variations --svg artifacts/evaluation/p_letter_disk_recheck_v1/independent.svg --description-file artifacts/evaluation/p_letter_disk_recheck_v1/independent.txt --seed 20261015 --output-dir .tmp/p-letter-plan-b-reproduce --keep-debug-artifacts
.venv/Scripts/python.exe artifacts/evaluation/labeled_disk_recheck_v1/recheck_archive_families.py --output-dir .tmp/p-letter-archive-reproduce
.venv/Scripts/python.exe artifacts/evaluation/spiral_disk_recheck_v1/run_standard_profile.py --output-dir .tmp/p-letter-standard-reproduce
$env:RUN_HEAVY_CONVERSION_TESTS = '1'
.venv/Scripts/python.exe -m pytest -q tests/test_labeled_disk_runtime.py tests/test_conversion_regression_smoke.py --basetemp .tmp/p-letter-focused-reproduce
.venv/Scripts/python.exe -m compileall -q src tests tools
.venv/Scripts/python.exe -m src.imageCompositeConverter --help
.venv/Scripts/python.exe -m tools.check_no_new_image_id_hardcoding
git -c core.whitespace=cr-at-eol diff --check
```

Das Paket versioniert Manifest, echte Baselines, finale Vektoren,
Quelleninventar, Gateberichte, unabhängige Vorlage und kompakte Belege beider
Variationsläufe. Vollständige Unterprozessartefakte bleiben unter
`.tmp/p-letter-*` erhalten.
