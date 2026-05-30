# Nächstes Arbeitspaket – Run ME (2026-05-30)

Dieses Arbeitspaket rotiert nach Run MD auf den nächsten dokumentierten
Plan-B-Kandidaten `AC0201_2.jpg` und ergänzt den beschreibungsgetriebenen
Geometry-IR-Pfad um ein kompaktes Kompressor-Symbol, damit der echte
Non-Composite-Call-Path die Beschreibung `Kompressor grau nach oben` als
strukturierte Vektorprimitive statt als generisches Element-Fit-Symbol rendert.

## 1) Nächste dokumentierte Aufgabe: AC0201-2-Kompressor als Geometry-IR

- Anlass:
  - `PLAN_B_KANDIDATEN.md` führte `AC0201_2.jpg` als nächsten einfachen
    Kompressor-Kandidaten.
  - Der vorgeschaltete Einzelrun erzeugte zwar ein SVG, protokollierte aber noch
    `status=non_composite_elementwise_symbol_fit` und nutzte damit die generische
    strukturierte Symbolannäherung statt der konkreten AC0201-Beschreibung.
- Umsetzung:
  - Die Beschreibungserkennung akzeptiert `Kompressor` nun als fachlichen
    Geometriehinweis, damit `Kompressor grau nach oben` nicht mehr als
    unzureichende Beschreibung aussortiert wird.
  - Die Geometry-IR erkennt aufwärts gerichtete Kompressor-Beschreibungen und
    erzeugt eine konkrete Symbolkette aus `CircleBackground` und
    `UpwardCompressorGlyph`.
  - Das Rendering zeichnet den grünen Kreis als stabile `compressor_circle`-
    Ellipse und die beiden grauen Aufwärtslinien als
    `upward_compressor_left_line` und `upward_compressor_right_line`.
  - Der Non-Composite-Fallback akzeptiert diese neuen beschreibungsgetriebenen
    Geometry-IR-Elemente im echten Call-Path.

## 2) Sichernde Detailtests

- Befehl:
  - `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_helpers.py tests/detailtests/test_description_contract_helpers.py tests/detailtests/test_non_composite_runtime_helpers.py`
- Ergebnis:
  - Exit `0`
  - `40 passed in 0.35s`
- Abdeckung:
  - AC0201-artige Beschreibungen werden als `CircleBackground` und
    `UpwardCompressorGlyph` gemappt.
  - Das SVG-Rendering enthält stabile IDs für den Kreis und beide aufwärts
    laufenden Kompressorlinien.
  - Der echte Non-Composite-Helfer wählt den
    `non_composite_description_geometry_ir`-Pfad für AC0201-artige
    Beschreibungen.

## 3) AC0201-2-Repro im externen Output-Verzeichnis

- Befehl:
  - `rm -rf /tmp/ic-ac0201-runme; PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ac0201-runme --start AC0201_2 --end AC0201_2 --deterministic-order`
- Ergebnis:
  - Exit `0`
  - `/tmp/ic-ac0201-runme/converted_svgs/AC0201_2.svg` wurde erzeugt.
  - Kein Failure-Eintrag in `/tmp/ic-ac0201-runme/reports/batch_failure_summary.csv`.
  - Validation-Log enthält `status=non_composite_description_geometry_ir`,
    `geometry_ir_element_count=2`, `CircleBackground` und
    `UpwardCompressorGlyph`.
  - Das SVG enthält die IDs `compressor_circle`,
    `upward_compressor_left_line` und `upward_compressor_right_line`.

## 4) Volltest

- Befehl:
  - `PYENV_VERSION=3.10.20 PYTHONPATH=vendor/linux-py310/site-packages:. timeout 300 python -m pytest -q -rs`
- Ergebnis:
  - Exit `0`
  - `579 passed, 5 warnings in 4.31s`

## Fazit

Der nächste dokumentierte Plan-B-Kandidat `AC0201_2.jpg` nutzt im echten
Call-Path nun eine beschreibungsgetriebene Geometry-IR mit explizitem grünem
Kreis und zwei grauen aufwärts gerichteten Kompressorlinien. Der Einzelrun
bleibt grün und die Vollsuite ist weiterhin stabil.
