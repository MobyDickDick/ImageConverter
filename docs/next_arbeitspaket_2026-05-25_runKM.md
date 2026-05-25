# Nächstes Arbeitspaket – Run KM (2026-05-25)

Dieses Arbeitspaket wurde im etablierten 3er-Schema durchgeführt.

## 1) Nächste dokumentierte Aufgabe

- Aufgabe: `TB-A3` timeout-gesichert isoliert erneut ausführen.
- Befehl:
  - `PYENV_VERSION=3.10.20 timeout 240 python -m pytest tests/test_satisfactory_regression_battery.py::test_satisfactory_successful_variants_reconversion_keeps_or_improves_quality -q`
- Ergebnis:
  - Exit `0`
  - `1 skipped, 5 warnings in 2.32s`
  - Log: `artifacts/converted_images/reports/TB_A3_timeout_probe_2026-05-25_runKM.log`

## 2) Gekoppelte Plan-B-Aufgabe

- Stabiler Re-Run der Plan-B-Syntheseprobe für `AC0040_S`.
- Befehl:
  - `PYTHONPATH=. python3 tools/plan_b_synthetic_probe.py "Bildbeschreibung: Kreis mit horizontalem Griff links und Beschriftung rF." --variant AC0040_S --output-dir artifacts/converted_images/reports`
- Ergebnis:
  - Exit `0`
  - `status=ok`
  - Log: `artifacts/converted_images/reports/AC0040_S_planb_synthetic_2026-05-25_runKM.log`

## 3) Einzellauf (Re-Run)

- Einzellauf für `AC0040_S` erneut durchgeführt.
- Befehl:
  - `PYTHONPATH=. timeout 240 python3 -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir artifacts/converted_images --start AC0040_S --end AC0040_S`
- Ergebnis:
  - Exit `0`
  - Log: `artifacts/converted_images/reports/AC0040_S_single_2026-05-25_runKM.log`

## Kurzfazit

Das nächste Arbeitspaket wurde in der 3er-Kombination vollständig als reproduzierbarer Re-Run ausgeführt. TB-A3 bleibt aktuell stabil (`skipped`, Exit `0`), die gekoppelte Plan-B-Aufgabe bleibt grün und der Einzellauf für `AC0040_S` läuft weiterhin erfolgreich durch.
