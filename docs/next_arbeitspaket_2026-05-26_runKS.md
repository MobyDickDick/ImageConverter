# Nächstes Arbeitspaket – Run KS (2026-05-26)

Dieses Arbeitspaket wurde im festen 3er-Schema inklusive finalem Volltest ausgeführt.

## 1) Nächste dokumentierte Aufgabe (TB-A3)
- Befehl:
  - `PYENV_VERSION=3.10.20 timeout 240 python -m pytest tests/test_satisfactory_regression_battery.py::test_satisfactory_successful_variants_reconversion_keeps_or_improves_quality -q`
- Ergebnis:
  - Exit `0`
  - `1 skipped, 5 warnings in 2.48s`
- Log:
  - `artifacts/converted_images/reports/TB_A3_timeout_probe_2026-05-26_runKS.log`

## 2) Gekoppelte Plan-B-Aufgabe
- Gewünschter Input `artifacts/images_to_convert/samples/AC0025.svg` ist im Repository nicht vorhanden.
- Ausführung stattdessen mit der vorhandenen SVG-Variante:
  - `PYTHONPATH=. python3 tools/plan_b_roundtrip.py artifacts/converted_images/converted_svgs/AC0025.svg --output-dir artifacts/converted_images/reports`
- Ergebnis:
  - Exit `0`
  - `variant=AC0025`, `delta2_output_vs_sample=154841.128165`
- Log:
  - `artifacts/converted_images/reports/AC0025_planb_roundtrip_2026-05-26_runKS.log`

## 3) Nächstes CSV-Bild
- Einzellauf:
  - `PYTHONPATH=. timeout 240 python3 -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir artifacts/converted_images --start AC0025 --end AC0025`
- Ergebnis:
  - Exit `0`
  - Fallback-Modus aktiv; Lauf abgeschlossen und Report-Kacheln aktualisiert.
- Log:
  - `artifacts/converted_images/reports/AC0025_single_2026-05-26_runKS.log`

## Volltest (final)
- Befehl:
  - `PYENV_VERSION=3.10.20 timeout 300 python -m pytest -q -rs`
- Ergebnis:
  - Exit `0`
  - `533 passed, 5 warnings in 6.42s`
- Log:
  - `artifacts/converted_images/reports/pytest_full_2026-05-26_runKS.log`

## Fazit
Das dokumentierte Arbeitspaket wurde durchgeführt. Plan B für AC0025 wurde ausgeführt (mit vorhandenem SVG-Ersatzpfad), der Einzellauf ist grün und der abschließende Volltest ebenfalls.
