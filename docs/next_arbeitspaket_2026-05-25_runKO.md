# Nächstes Arbeitspaket – Run KO (2026-05-25)

Dieses Arbeitspaket wurde vollständig im etablierten 3er-Schema inklusive Volltest ausgeführt.

## 1) Nächste dokumentierte Aufgabe

- Aufgabe: `TB-A3` timeout-gesichert erneut ausführen.
- Befehl:
  - `PYENV_VERSION=3.10.20 timeout 240 python -m pytest tests/test_satisfactory_regression_battery.py::test_satisfactory_successful_variants_reconversion_keeps_or_improves_quality -q`
- Ergebnis:
  - Exit `0`
  - `1 skipped, 5 warnings in 2.49s`
  - Log: `artifacts/converted_images/reports/TB_A3_timeout_probe_2026-05-25_runKO.log`

## 2) Gekoppelte Plan-B-Aufgabe

- Stabiler Re-Run der Plan-B-Syntheseprobe für `AC0050_S`.
- Befehl:
  - `PYTHONPATH=. python3 tools/plan_b_synthetic_probe.py "Bildbeschreibung: Kreis mit horizontalem Griff links und Beschriftung rF." --variant AC0050_S --output-dir artifacts/converted_images/reports`
- Ergebnis:
  - Exit `0`
  - `status=ok`
  - Log: `artifacts/converted_images/reports/AC0050_S_planb_synthetic_2026-05-25_runKO.log`

## 3) Einzellauf (Re-Run)

- Einzellauf für `AC0050_S` erneut durchgeführt.
- Befehl:
  - `PYTHONPATH=. timeout 240 python3 -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir artifacts/converted_images --start AC0050_S --end AC0050_S`
- Ergebnis:
  - Exit `0`
  - Log: `artifacts/converted_images/reports/AC0050_S_single_2026-05-25_runKO.log`

## Volltest (alle Tests)

- Befehl:
  - `PYENV_VERSION=3.10.20 timeout 300 python -m pytest -q -rs`
- Ergebnis:
  - Exit `0`
  - `531 passed, 5 warnings in 6.32s`
  - Log: `artifacts/converted_images/reports/pytest_full_2026-05-25_runKO.log`

## Kurzfazit

Das nächste Arbeitspaket wurde vollständig durchgeführt. TB-A3 bleibt stabil, die gekoppelte Plan-B-Aufgabe ist grün, der Einzellauf für `AC0050_S` läuft erfolgreich, und der vollständige Testsatz ist grün.
