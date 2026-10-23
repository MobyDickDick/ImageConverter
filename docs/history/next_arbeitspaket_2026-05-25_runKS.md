# Nächstes Arbeitspaket – Run KS (2026-05-25)

Dieses Arbeitspaket wurde vollständig im festen 3er-Schema inklusive finalem Volltest ausgeführt.

## 1) Nächste dokumentierte Aufgabe (TB-A3)
- Befehl:
  - `PYENV_VERSION=3.10.20 timeout 240 python -m pytest tests/test_satisfactory_regression_battery.py::test_satisfactory_successful_variants_reconversion_keeps_or_improves_quality -q`
- Ergebnis:
  - Exit `0`
  - `1 skipped, 5 warnings in 2.15s`
- Log:
  - `artifacts/converted_images/reports/TB_A3_timeout_probe_2026-05-25_runKS.log`

## 2) Gekoppelte Plan-B-Aufgabe
- Befehl:
  - `PYTHONPATH=. python3 tools/plan_b_synthetic_probe.py "Bildbeschreibung: Kreis mit horizontalem Griff links und Beschriftung rF." --variant AC0120_S --output-dir artifacts/converted_images/reports`
- Ergebnis:
  - Exit `0`
  - `status=ok`, `variant=AC0120_S`
- Log:
  - `artifacts/converted_images/reports/AC0120_S_planb_synthetic_2026-05-25_runKS.log`

## 3) Nächstes CSV-Bild
- Einzellauf:
  - `PYTHONPATH=. timeout 240 python3 -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir artifacts/converted_images --start AC0120_S --end AC0120_S`
- Ergebnis:
  - Exit `0`
- Log:
  - `artifacts/converted_images/reports/AC0120_S_single_2026-05-25_runKS.log`

## Volltest (final)
- Befehl:
  - `PYENV_VERSION=3.10.20 timeout 300 python -m pytest -q -rs`
- Ergebnis:
  - Exit `0`
  - `531 passed, 5 warnings in 5.49s`
- Log:
  - `artifacts/converted_images/reports/pytest_full_2026-05-25_runKS.log`

## Fazit
Das nächste Arbeitspaket wurde vollständig durchgeführt; TB-A3, die gekoppelte Plan-B-Aufgabe, der Einzellauf sowie der abschließende Volltest sind grün.
