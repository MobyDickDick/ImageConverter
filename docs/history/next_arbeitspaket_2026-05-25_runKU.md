# Nächstes Arbeitspaket – Run KU (2026-05-25)

Dieses Arbeitspaket wurde vollständig im festen 3er-Schema inklusive finalem Volltest ausgeführt.

## 1) Nächste dokumentierte Aufgabe (TB-A3)
- Befehl:
  - `PYENV_VERSION=3.10.20 timeout 240 python -m pytest tests/test_satisfactory_regression_battery.py::test_satisfactory_successful_variants_reconversion_keeps_or_improves_quality -q`
- Ergebnis:
  - Exit `0`
  - `1 skipped, 5 warnings in 2.37s`
- Log:
  - `artifacts/converted_images/reports/TB_A3_timeout_probe_2026-05-25_runKU.log`

## 2) Gekoppelte Plan-B-Aufgabe (Plan B mit AC0060_L.svg)
- Befehl:
  - `PYTHONPATH=. python3 tools/plan_b_roundtrip.py artifacts/images_to_convert/samples/AC0060_L.svg --output-dir artifacts/converted_images/reports`
- Ergebnis:
  - Exit `0`
  - `variant=AC0060_L`
  - `delta2_output_vs_sample=1695.742597`
- Log:
  - `artifacts/converted_images/reports/AC0060_L_planb_roundtrip_2026-05-25_runKU.log`

## 3) Nächstes CSV-Bild
- Einzellauf:
  - `PYTHONPATH=. timeout 240 python3 -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir artifacts/converted_images --start AC0060_L --end AC0060_L`
- Ergebnis:
  - Exit `0`
- Log:
  - `artifacts/converted_images/reports/AC0060_L_single_2026-05-25_runKU.log`

## Volltest (final)
- Befehl:
  - `PYENV_VERSION=3.10.20 timeout 300 python -m pytest -q -rs`
- Ergebnis:
  - Exit `0`
  - `533 passed, 5 warnings in 6.18s`
- Log:
  - `artifacts/converted_images/reports/pytest_full_2026-05-25_runKU.log`

## Fazit
Das nächste Arbeitspaket wurde vollständig durchgeführt; TB-A3, die gekoppelte Plan-B-Aufgabe auf Basis von `AC0060_L.svg`, der Einzellauf sowie der abschließende Volltest sind grün.
