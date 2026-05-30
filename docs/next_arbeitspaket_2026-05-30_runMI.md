# Nächstes Arbeitspaket – Run MI (2026-05-30)

Dieses Arbeitspaket rotiert nach Run MH auf den nächsten dokumentierten
Plan-B-Kandidaten `AC0211_S.jpg` und sichert dessen im XML dokumentierte
Beschreibung `Kopressor grau nach oben` trotz Schreibvariante explizit im
beschreibungsgetriebenen Geometry-IR-Pfad ab.

## 1) Nächste dokumentierte Aufgabe: AC0211-S-Kopressor als Geometry-IR

- Anlass:
  - `PLAN_B_KANDIDATEN.md` benennt nach `AC0204_S_sia.jpg` den nächsten
    Kandidaten `AC0211_S.jpg`.
  - Die Beschreibung im XML lautet `Kopressor grau nach oben`; die fachliche
    AC02-Kompressor-Geometrie soll auch mit dieser Schreibvariante im echten
    Non-Composite-Call-Path als strukturierte Vektorprimitive laufen.
- Umsetzung:
  - Die Geometry-IR erkennt `Kopressor` nun zusätzlich zu `Kompressor` als
    Kompressor-Hinweis.
  - Der Description-Contract zählt die Schreibvariante als Geometriebegriff,
    sodass der Parser die Beschreibung nicht mehr als `insufficient_description`
    einstuft.
  - Neue Regressionsfälle sichern Mapping, SVG-Rendering und den echten
    Non-Composite-Helfer für `AC0211_S`.

## 2) Sichernde Detailtests

- Befehl:
  - `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_helpers.py tests/detailtests/test_description_contract_helpers.py tests/detailtests/test_non_composite_runtime_helpers.py`
- Ergebnis:
  - Exit `0`
  - `55 passed in 0.38s`
- Abdeckung:
  - `Kopressor grau nach oben` wird als `CircleBackground` und
    `UpwardCompressorGlyph` gemappt.
  - Das SVG-Rendering enthält die stabilen IDs `compressor_circle`,
    `upward_compressor_left_line` und `upward_compressor_right_line`.
  - Der echte Non-Composite-Helfer wählt für `AC0211_S` den
    `non_composite_description_geometry_ir`-Pfad.

## 3) AC0211-S-Repro im externen Output-Verzeichnis

- Befehl:
  - `rm -rf /tmp/ic-ac0211-runmi; PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ac0211-runmi --start AC0211_S --end AC0211_S --deterministic-order`
- Ergebnis:
  - Exit `0`
  - Kein Failure-Eintrag in `/tmp/ic-ac0211-runmi/reports/batch_failure_summary.csv`.
  - Element-Validation-Log enthält `status=non_composite_description_geometry_ir`,
    `geometry_ir_element_count=2`, `CircleBackground` und
    `UpwardCompressorGlyph`.
  - Das erzeugte SVG enthält die IDs `compressor_circle`,
    `upward_compressor_left_line` und `upward_compressor_right_line`.

## 4) Volltest

- Befehl:
  - `PYENV_VERSION=3.10.20 PYTHONPATH=vendor/linux-py310/site-packages:. timeout 300 python -m pytest -q -rs`
- Ergebnis:
  - Exit `0`
  - `594 passed, 5 warnings in 6.20s`

## 5) Kandidatenrotation

- `PLAN_B_KANDIDATEN.md` wurde nach erledigtem `AC0211_S.jpg` auf
  `AC0212_L.jpg` rotiert und mit `AC0213_L.jpg` als weiterem AC02-Kandidaten
  aufgefüllt.

## Fazit

Der nächste dokumentierte Plan-B-Kandidat `AC0211_S.jpg` nutzt trotz der
XML-Schreibvariante `Kopressor` den beschreibungsgetriebenen Geometry-IR-Pfad
mit explizitem Kreis und zwei aufwärts gerichteten Kompressorlinien. Die
Kandidatenliste zeigt anschließend `AC0212_L.jpg` als nächste Rotation.
