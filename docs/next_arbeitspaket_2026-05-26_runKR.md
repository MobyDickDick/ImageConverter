# Nächstes Arbeitspaket – Run KR (2026-05-26)

Dieses Arbeitspaket wurde vollständig im festen 3er-Schema inklusive finalem Volltest ausgeführt.

## 1) Nächste dokumentierte Aufgabe (TB-A3)
- Befehl:
  - `PYENV_VERSION=3.10.20 timeout 240 python -m pytest tests/test_satisfactory_regression_battery.py::test_satisfactory_successful_variants_reconversion_keeps_or_improves_quality -q`
- Ergebnis:
  - Exit `0`
  - `1 skipped, 5 warnings in 2.51s`
- Log:
  - `artifacts/converted_images/reports/TB_A3_timeout_probe_2026-05-26_runKR.log`

## 2) Gekoppelte Plan-B-Aufgabe
- Befehl:
  - `PYTHONPATH=. python3 tools/plan_b_roundtrip.py artifacts/images_to_convert/samples/AC0100_L.svg --output-dir artifacts/converted_images/reports`
- Ergebnis:
  - Exit `0`
  - `variant=AC0100_L`, `delta2_output_vs_sample=3245.435702`
- Log:
  - `artifacts/converted_images/reports/AC0100_L_planb_roundtrip_2026-05-26_runKR.log`

## 3) Nächstes CSV-Bild
- Einzellauf:
  - `PYTHONPATH=. timeout 240 python3 -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir artifacts/converted_images --start AC0100_L --end AC0100_L`
- Ergebnis:
  - Exit `0`
  - Plan-B-Vergleich aktiv mit Sample-Vorteil (`err=182.491`, `baseline=194.517`).
- Log:
  - `artifacts/converted_images/reports/AC0100_L_single_2026-05-26_runKR.log`

## Volltest (final)
- Befehl:
  - `PYENV_VERSION=3.10.20 timeout 300 python -m pytest -q -rs`
- Ergebnis:
  - Exit `0`
  - `533 passed, 5 warnings in 6.03s`
- Log:
  - `artifacts/converted_images/reports/pytest_full_2026-05-26_runKR.log`

## Fazit
Das nächste Arbeitspaket wurde vollständig durchgeführt; TB-A3, die gekoppelte Plan-B-Aufgabe, der Einzellauf sowie der abschließende Volltest sind grün.
