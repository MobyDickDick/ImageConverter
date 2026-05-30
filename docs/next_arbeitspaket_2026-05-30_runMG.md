# Nächstes Arbeitspaket – Run MG (2026-05-30)

Dieses Arbeitspaket rotiert nach Run MF auf den nächsten dokumentierten
Plan-B-Kandidaten `AC0203_1.jpg` und erweitert den beschreibungsgetriebenen
Geometry-IR-Pfad um die hauptdiagonal gespiegelte Kompressor-Variante, damit der
echte Non-Composite-Call-Path die Beschreibung `Wie AC0202: Kompressor grau nach
rechts. Geometrische Variante: Hauptdiagonal gespiegelt.` als strukturierte
Vektorprimitive statt als generisches Element-Fit-Symbol rendert.

## 1) Nächste dokumentierte Aufgabe: AC0203-1-Kompressor als Geometry-IR

- Anlass:
  - `PLAN_B_KANDIDATEN.md`/die laufende Aufgabenrotation benennt nach
    `AC0202_2.jpg` den nächsten Kompressor-Kandidaten `AC0203_1.jpg`.
  - Der Kandidat beschreibt dieselbe AC02-Kompressor-Familie, aber als
    hauptdiagonal gespiegelte, rot hinterlegte Liniengeometrie.
- Umsetzung:
  - Die Geometry-IR erkennt `Kompressor ... nach rechts` zusammen mit
    `Hauptdiagonal gespiegelt` nun als konkrete Symbolkette aus
    `CircleBackground` und `MainDiagonalMirroredCompressorGlyph`.
  - Das Rendering zeichnet den roten Kreis als stabile `compressor_circle`-
    Ellipse und die beiden hellen, nach unten laufenden gespiegelten Linien als
    `mirrored_compressor_left_line` und `mirrored_compressor_right_line`.
  - Der Non-Composite-Fallback akzeptiert das neue
    `MainDiagonalMirroredCompressorGlyph` als beschreibungsgetriebenes
    Geometry-IR-Element im echten Call-Path.

## 2) Sichernde Detailtests

- Befehl:
  - `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_helpers.py tests/detailtests/test_description_contract_helpers.py tests/detailtests/test_non_composite_runtime_helpers.py`
- Ergebnis:
  - Exit `0`
  - `48 passed in 0.53s`
- Abdeckung:
  - AC0203-artige Beschreibungen werden als `CircleBackground` und
    `MainDiagonalMirroredCompressorGlyph` gemappt.
  - Das SVG-Rendering enthält stabile IDs für den Kreis und beide gespiegelten
    Kompressorlinien.
  - Der echte Non-Composite-Helfer wählt den
    `non_composite_description_geometry_ir`-Pfad für AC0203-artige
    Beschreibungen.

## 3) AC0203-1-Repro im externen Output-Verzeichnis

- Befehl:
  - `rm -rf /tmp/ic-ac0203-runmg; PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ac0203-runmg --start AC0203_1 --end AC0203_1 --deterministic-order`
- Ergebnis:
  - Exit `0`
  - `/tmp/ic-ac0203-runmg/converted_svgs/AC0203_1.svg` wurde erzeugt.
  - Kein Failure-Eintrag in
    `/tmp/ic-ac0203-runmg/reports/batch_failure_summary.csv`.
  - Element-Validation-Log enthält `status=non_composite_description_geometry_ir`,
    `geometry_ir_element_count=2`, `CircleBackground` und
    `MainDiagonalMirroredCompressorGlyph`.
  - Das SVG enthält die IDs `compressor_circle`,
    `mirrored_compressor_left_line` und `mirrored_compressor_right_line`.

## 4) Volltest

- Befehl:
  - `PYENV_VERSION=3.10.20 PYTHONPATH=vendor/linux-py310/site-packages:. timeout 300 python -m pytest -q -rs`
- Ergebnis:
  - Exit `0`
  - `587 passed, 5 warnings in 4.90s`

## Fazit

Der nächste dokumentierte Plan-B-Kandidat `AC0203_1.jpg` nutzt im echten
Call-Path nun eine beschreibungsgetriebene Geometry-IR mit explizitem rotem
Kreis und zwei hauptdiagonal gespiegelten Kompressorlinien. Der Einzelrun bleibt
grün und die Vollsuite ist weiterhin stabil.
