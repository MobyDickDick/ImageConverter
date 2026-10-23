# Nächstes Arbeitspaket – Run LN (2026-05-28)

Dieses Arbeitspaket bearbeitet den in `docs/open_tasks.md` priorisierten PR-R2-Schritt der Ketten-Architektur.

## 1) PR-R2 Geometry-IR

- Eingeführtes Modul:
  - `src/iCCModules/imageCompositeConverterGeometryIr.py`
- Umgesetzte IR-Primitive:
  - `HorizontalGradient`
  - `RectBorder`
  - `DiagonalBand`
  - `PlusGlyph`
  - `MinusGlyph`
- Mapping:
  - Beschreibungen mit Rechteck-/Gradient-/Diagonal-/Plus-Minus-Hinweisen werden in eine geordnete IR-Kette übersetzt.
  - AC0120-artige Self-Reference-Beschreibungen erhalten eine explizite Rect-/Diagonal-/Plus-Minus-Kette.
- Verdrahtung:
  - `Reflection.parseDescription(...)` legt die Kette in `params["geometry_ir"]` ab.
  - `generateCompositeSvgImpl(...)` rendert vorhandene IR-Ketten zentral über den Geometry-IR-Renderer.

## 2) Tests

- Befehl:
  - `PYENV_VERSION=3.10.20 python -m pytest -q tests/detailtests/test_geometry_ir_helpers.py tests/detailtests/test_description_contract_helpers.py tests/detailtests/test_composite_svg_helpers.py`
- Ergebnis:
  - Exit `0`
  - `10 passed in 0.18s`
- Log:
  - `artifacts/converted_images/reports/pr_r2_geometry_ir_detailtests_2026-05-28_runLN.log`

## 3) Volltest

- Befehl:
  - `PYENV_VERSION=3.10.20 timeout 300 python -m pytest -q -rs`
- Ergebnis:
  - Exit `0`
  - `551 passed, 5 warnings in 3.84s`
- Log:
  - `artifacts/converted_images/reports/pytest_full_2026-05-28_runLN.log`

## Fazit

PR-R2 ist implementiert; PR-R3 kann auf der nun vorhandenen `geometry_ir`-Kette aufsetzen.
