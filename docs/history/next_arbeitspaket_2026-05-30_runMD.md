# Nächstes Arbeitspaket – Run MD (2026-05-30)

Dieses Arbeitspaket rotiert nach Run MC auf den nächsten dokumentierten
Plan-B-Kandidaten `AC0160_L.jpg` und nutzt den vorhandenen beschreibungs-
getriebenen Geometry-IR-Pfad, damit der echte Non-Composite-Call-Path die
Differenzdruckmessung als strukturierte Vektorprimitive statt als generisches
Element-Fit-Symbol rendert.

## 1) Nächste dokumentierte Aufgabe: AC0160-L-Beschreibung als Geometry-IR

- Anlass:
  - `PLAN_B_KANDIDATEN.md` führte `AC0160_L.jpg` als nächsten einfachen
    L-Kandidaten.
  - Der vorgeschaltete Einzelrun erzeugte zwar ein SVG, protokollierte aber noch
    `status=non_composite_elementwise_symbol_fit` und nutzte damit die generische
    strukturierte Symbolannäherung statt der konkreten AC0160-Beschreibung.
- Umsetzung:
  - Die Geometry-IR erkennt AC0160-artige Beschreibungen mit
    `Differenzdruckmessung`, `dp` und `doppelten grauen Rand` als konkrete
    Symbolkette.
  - Das halbe Rechteck mit doppeltem grauem Rand wird als neues
    `HalfDoubleRectBorder`-IR-Element gerendert.
  - Das obere kleine graue Rechteck wird als `LabelBox` und die `dp`-Beschriftung
    als `TextGlyph` gerendert.
  - Der Non-Composite-Fallback akzeptiert diese neuen beschreibungsgetriebenen
    Geometry-IR-Elemente im echten Call-Path.

## 2) Sichernde Detailtests

- Befehl:
  - `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_helpers.py tests/detailtests/test_description_contract_helpers.py tests/detailtests/test_non_composite_runtime_helpers.py`
- Ergebnis:
  - Exit `0`
  - `36 passed in 0.32s`
- Abdeckung:
  - AC0160-artige Beschreibungen werden als `HalfDoubleRectBorder`, `LabelBox`
    und `TextGlyph` gemappt.
  - Das SVG-Rendering enthält stabile IDs für äußeren/inneren Doppelrand, die
    linke Halbmaskierung, die Label-Box und den `dp`-Text.
  - Der echte Non-Composite-Helfer wählt den
    `non_composite_description_geometry_ir`-Pfad für AC0160-artige Beschreibungen.

## 3) AC0160-L-Repro im externen Output-Verzeichnis

- Befehl:
  - `rm -rf /tmp/ic-ac0160-runmd; PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ac0160-runmd --start AC0160_L --end AC0160_L --deterministic-order`
- Ergebnis:
  - Exit `0`
  - `/tmp/ic-ac0160-runmd/converted_svgs/AC0160_L.svg` wurde erzeugt.
  - Kein Failure-Eintrag in `/tmp/ic-ac0160-runmd/reports/batch_failure_summary.csv`.
  - Validation-Log enthält `status=non_composite_description_geometry_ir`,
    `geometry_ir_element_count=3`, `HalfDoubleRectBorder`, `LabelBox` und
    `TextGlyph`.
  - Das SVG enthält die IDs `half_double_rect_outer`, `half_double_rect_inner`,
    `half_double_rect_left_half_mask`, `dp_label_box` und `dp_label_text`.

## 4) Volltest

- Befehl:
  - `PYENV_VERSION=3.10.20 PYTHONPATH=vendor/linux-py310/site-packages:. timeout 300 python -m pytest -q -rs`
- Ergebnis:
  - Exit `0`
  - `575 passed, 5 warnings in 4.48s`

## Fazit

Der nächste dokumentierte Plan-B-Kandidat `AC0160_L.jpg` nutzt im echten
Call-Path nun eine beschreibungsgetriebene Geometry-IR mit explizitem halbem
Doppelrand-Rechteck, oberer Label-Box und `dp`-Beschriftung. Der Einzelrun bleibt
grün und die Vollsuite ist weiterhin stabil.
