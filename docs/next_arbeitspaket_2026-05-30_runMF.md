# Nächstes Arbeitspaket – Run MF (2026-05-30)

Dieses Arbeitspaket rotiert nach Run ME auf den nächsten dokumentierten
Plan-B-Kandidaten `AC0202_2.jpg` und erweitert den beschreibungsgetriebenen
Geometry-IR-Pfad um ein nach rechts gerichtetes Kompressor-Symbol, damit der
echte Non-Composite-Call-Path die Beschreibung `Kompressor grau nach rechts` als
strukturierte Vektorprimitive statt als generisches Element-Fit-Symbol rendert.

## 1) Nächste dokumentierte Aufgabe: AC0202-2-Kompressor als Geometry-IR

- Anlass:
  - `PLAN_B_KANDIDATEN.md`/die laufende Aufgabenrotation benennt nach
    `AC0201_2.jpg` den nächsten Kompressor-Kandidaten `AC0202_2.jpg`.
  - Der Kandidat beschreibt dieselbe Kompressor-Familie, aber mit
    horizontal gespiegelter bzw. nach rechts gerichteter Liniengeometrie.
- Umsetzung:
  - Die Geometry-IR erkennt `Kompressor ... nach rechts` nun als konkrete
    Symbolkette aus `CircleBackground` und `RightwardCompressorGlyph`.
  - Das Rendering zeichnet den grünen Kreis als stabile `compressor_circle`-
    Ellipse und die beiden hellen, nach rechts laufenden Linien als
    `rightward_compressor_upper_line` und `rightward_compressor_lower_line`.
  - Der Non-Composite-Fallback akzeptiert das neue
    `RightwardCompressorGlyph` als beschreibungsgetriebenes Geometry-IR-Element
    im echten Call-Path.

## 2) Sichernde Detailtests

- Befehl:
  - `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_helpers.py tests/detailtests/test_description_contract_helpers.py tests/detailtests/test_non_composite_runtime_helpers.py`
- Ergebnis:
  - Exit `0`
  - `44 passed in 0.35s`
- Abdeckung:
  - AC0202-artige Beschreibungen werden als `CircleBackground` und
    `RightwardCompressorGlyph` gemappt.
  - Das SVG-Rendering enthält stabile IDs für den Kreis und beide nach rechts
    laufenden Kompressorlinien.
  - Der echte Non-Composite-Helfer wählt den
    `non_composite_description_geometry_ir`-Pfad für AC0202-artige
    Beschreibungen.

## 3) AC0202-2-Repro im externen Output-Verzeichnis

- Befehl:
  - `rm -rf /tmp/ic-ac0202-runmf; PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ac0202-runmf --start AC0202_2 --end AC0202_2 --deterministic-order`
- Ergebnis:
  - Exit `0`
  - `/tmp/ic-ac0202-runmf/converted_svgs/AC0202_2.svg` wurde erzeugt.
  - Kein Failure-Eintrag in
    `/tmp/ic-ac0202-runmf/reports/batch_failure_summary.csv`.
  - Element-Validation-Log enthält `status=non_composite_description_geometry_ir`,
    `geometry_ir_element_count=2`, `CircleBackground` und
    `RightwardCompressorGlyph`.
  - Das SVG enthält die IDs `compressor_circle`,
    `rightward_compressor_upper_line` und `rightward_compressor_lower_line`.

## 4) Volltest

- Befehl:
  - `PYENV_VERSION=3.10.20 PYTHONPATH=vendor/linux-py310/site-packages:. timeout 300 python -m pytest -q -rs`
- Ergebnis:
  - Exit `0`
  - `583 passed, 5 warnings in 3.64s`

## Fazit

Der nächste dokumentierte Plan-B-Kandidat `AC0202_2.jpg` nutzt im echten
Call-Path nun eine beschreibungsgetriebene Geometry-IR mit explizitem grünem
Kreis und zwei nach rechts gerichteten Kompressorlinien. Der Einzelrun bleibt
grün und die Vollsuite ist weiterhin stabil.
