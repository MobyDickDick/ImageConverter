# Nächstes Arbeitspaket – Run MH (2026-05-30)

Dieses Arbeitspaket rotiert nach Run MG auf den nächsten dokumentierten
Plan-B-Kandidaten `AC0204_S_sia.jpg` und sichert die bereits über AC0201
beschriebene identische Referenzgeometrie explizit im
beschreibungsgetriebenen Geometry-IR-Pfad ab.

## 1) Nächste dokumentierte Aufgabe: AC0204-S-sia als AC0201-Referenz-Geometry-IR

- Anlass:
  - `PLAN_B_KANDIDATEN.md` benennt nach `AC0203_1.jpg` den nächsten
    Kandidaten `AC0204_S_sia.jpg`.
  - Die Beschreibung lautet `Wie AC0201: Kompressor grau nach oben.
    Geometrische Variante: identisch zur Referenz.` und soll im echten
    Non-Composite-Call-Path weiterhin als strukturierte Vektorprimitive
    laufen.
- Umsetzung:
  - Neue Regressionsfälle sichern, dass diese AC0204-Beschreibung zu
    `CircleBackground` und `UpwardCompressorGlyph` gemappt wird.
  - Das SVG-Rendering wird für den AC0204-S-sia-Bildmaßstab auf die stabilen
    IDs `compressor_circle`, `upward_compressor_left_line` und
    `upward_compressor_right_line` geprüft.
  - Der echte Non-Composite-Helfer wird mit `AC0204_S_sia` abgesichert und
    protokolliert `status=non_composite_description_geometry_ir`.

## 2) Sichernde Detailtests

- Befehl:
  - `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_helpers.py tests/detailtests/test_description_contract_helpers.py tests/detailtests/test_non_composite_runtime_helpers.py`
- Ergebnis:
  - Exit `0`
  - `51 passed in 0.53s`
- Abdeckung:
  - AC0204-Identisch-zur-Referenz-Beschreibungen werden als
    `CircleBackground` und `UpwardCompressorGlyph` gemappt.
  - Das SVG-Rendering enthält stabile IDs für Kreis und beide aufwärts
    gerichteten Kompressorlinien.
  - Der echte Non-Composite-Helfer wählt für `AC0204_S_sia` den
    `non_composite_description_geometry_ir`-Pfad.

## 3) AC0204-S-sia-Repro im externen Output-Verzeichnis

- Befehl:
  - `rm -rf /tmp/ic-ac0204-runmh; PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ac0204-runmh --start AC0204_S_sia --end AC0204_S_sia --deterministic-order`
- Ergebnis:
  - Exit `0`
  - Kein Failure-Eintrag in `/tmp/ic-ac0204-runmh/reports/batch_failure_summary.csv`.
  - Element-Validation-Log enthält `status=non_composite_description_geometry_ir`,
    `geometry_ir_element_count=2`, `CircleBackground` und
    `UpwardCompressorGlyph`.

## 4) Volltest

- Befehl:
  - `PYENV_VERSION=3.10.20 PYTHONPATH=vendor/linux-py310/site-packages:. timeout 300 python -m pytest -q -rs`
- Ergebnis:
  - Exit `0`
  - `590 passed, 5 warnings in 5.92s`

## 5) Kandidatenrotation

- `PLAN_B_KANDIDATEN.md` wurde nach erledigtem `AC0204_S_sia.jpg` auf
  `AC0211_S.jpg` rotiert und mit `AC0212_L.jpg` als weiterem AC02-Kandidaten
  aufgefüllt.

## Fazit

Der nächste dokumentierte Plan-B-Kandidat `AC0204_S_sia.jpg` bleibt im echten
Call-Path auf der beschreibungsgetriebenen Geometry-IR und ist nun mit eigenen
AC0204-Regressionsfällen abgesichert. Die Kandidatenliste zeigt anschließend
`AC0211_S.jpg` als nächste Rotation.
