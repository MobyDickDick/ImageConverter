# Nächstes Arbeitspaket – Run MN (2026-05-30)

Dieses Arbeitspaket rotiert nach Run MM auf den nächsten dokumentierten
Plan-B-Kandidaten `AC0222_S.jpg` und schärft den beschreibungsgetriebenen
Geometry-IR-Pfad für den Kompressor mit grauem Hintergrund. Damit rendert der
echte Non-Composite-Call-Path die Beschreibung `Kompressor grauer Hintergrund
nach oben.` als strukturierte Vektorprimitive mit grauem Kreis und dunklen
Kompressorlinien statt als generisches Placeholder-/Element-Fit-Symbol.

## 1) Nächste dokumentierte Aufgabe: AC0222-S-Kompressor mit grauem Hintergrund als Geometry-IR

- Anlass:
  - `PLAN_B_KANDIDATEN.md` benennt nach `AC0221_S.jpg` den nächsten Kandidaten
    `AC0222_S.jpg`.
  - Die XML-Beschreibung nennt einen nach oben gerichteten Kompressor mit
    grauem Hintergrund; bisher wurde der echte Repro als
    `non_composite_pure_svg_placeholder_vector` protokolliert.
- Umsetzung:
  - Die Geometry-IR erkennt `Kompressor grauer Hintergrund nach oben` nun als
    bestehenden `CircleBackground` + `UpwardCompressorGlyph`-Kompressorfall,
    aber mit grauem Kreis-Fill `#d8d8d8` statt grünem Kompressor-Kreis.
  - Die beiden aufwärts gerichteten Kompressorlinien werden für diesen
    Grau-Hintergrund-Fall mit dunklem Stroke `#666666` gerendert, damit sie auf
    dem hellgrauen Kreis sichtbar und dem Original näher sind.
  - Der echte Non-Composite-Fallback wählt dadurch den bestehenden
    `non_composite_description_geometry_ir`-Pfad für `AC0222_S`.

## 2) Sichernde Detailtests

- Befehl:
  - `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_helpers.py tests/detailtests/test_description_contract_helpers.py tests/detailtests/test_non_composite_runtime_helpers.py`
- Ergebnis:
  - Exit `0`
  - `75 passed in 0.91s`
- Abdeckung:
  - AC0222-artige Beschreibungen werden als `CircleBackground` und
    `UpwardCompressorGlyph` gemappt.
  - Das SVG-Rendering enthält stabile IDs für Kreis sowie linke/rechte
    Kompressorlinie und nutzt die grauen AC0222-Farben `#d8d8d8` und `#666666`.
  - Der echte Non-Composite-Helfer wählt für `AC0222_S` den
    `non_composite_description_geometry_ir`-Pfad.

## 3) AC0222-S-Repro im externen Output-Verzeichnis

- Befehl:
  - `rm -rf /tmp/ic-ac0222-runmn; PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ac0222-runmn --start AC0222_S --end AC0222_S --deterministic-order`
- Ergebnis:
  - Exit `0`
  - Kein Failure-Eintrag in `/tmp/ic-ac0222-runmn/reports/batch_failure_summary.csv`.
  - Element-Validation-Log enthält `status=non_composite_description_geometry_ir`,
    `geometry_ir_element_count=2`, `CircleBackground` und `UpwardCompressorGlyph`.
  - Das erzeugte SVG enthält die IDs `compressor_circle`,
    `upward_compressor_left_line` und `upward_compressor_right_line` sowie die
    AC0222-Farben `#d8d8d8` und `#666666`.

## 4) Volltest

- Befehl:
  - `PYENV_VERSION=3.10.20 PYTHONPATH=vendor/linux-py310/site-packages:. timeout 300 python -m pytest -q -rs`
- Ergebnis:
  - Exit `0`
  - `618 passed, 5 warnings in 6.70s`

## 5) Kandidatenrotation

- `PLAN_B_KANDIDATEN.md` wurde nach erledigtem `AC0222_S.jpg` auf
  `AC0224_S.jpg` rotiert und mit `AC0231_S.jpg` als weiterem AC02-Kandidaten
  aufgefüllt.

## Fazit

Der nächste dokumentierte Plan-B-Kandidat `AC0222_S.jpg` nutzt im echten
Call-Path nun eine beschreibungsgetriebene Geometry-IR mit grauem Kreis und zwei
aufwärts gerichteten Kompressorlinien. Die Kandidatenliste zeigt anschließend
`AC0224_S.jpg` als nächste Rotation.
