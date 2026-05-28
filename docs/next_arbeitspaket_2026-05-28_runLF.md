# Nächstes Arbeitspaket – Run LF (2026-05-28)

Dieses Arbeitspaket wurde im 3er-Schema ausgeführt und mit Volltest abgeschlossen.

## 1) Nächste dokumentierte Aufgabe (TB-A3)

- Befehl:
  - `PYENV_VERSION=3.10.20 PYTHONPATH=vendor/linux-py310/site-packages:. timeout 240 python -m pytest tests/test_satisfactory_regression_battery.py::test_satisfactory_successful_variants_reconversion_keeps_or_improves_quality -q`
- Ergebnis:
  - Exit `0`
  - `1 skipped, 5 warnings in 2.37s`
- Log:
  - `artifacts/converted_images/reports/TB_A3_timeout_probe_2026-05-28_runLF.log`

## 2) Gekoppelte Plan-B-Aufgabe

- Befehl:
  - `PYENV_VERSION=3.10.20 PYTHONPATH=vendor/linux-py310/site-packages:. python tools/plan_b_roundtrip.py artifacts/images_to_convert/samples/AC0223_L.svg --output-dir artifacts/converted_images/reports`
- Ergebnis:
  - Exit `0`
  - `variant=AC0223_L`, `delta2_output_vs_sample=363.945213`
- Log:
  - `artifacts/converted_images/reports/AC0223_L_planb_roundtrip_2026-05-28_runLF.log`

## 3) Volltest (alle Tests)

- Befehl:
  - `PYENV_VERSION=3.10.20 PYTHONPATH=vendor/linux-py310/site-packages:. timeout 300 python -m pytest -q -rs`
- Ergebnis:
  - Exit `0`
  - `547 passed, 5 warnings in 6.18s`
- Log:
  - `artifacts/converted_images/reports/pytest_full_2026-05-28_runLF.log`

## Fazit

Das nächste dokumentierte Arbeitspaket (TB-A3 inkl. Plan-B) wurde abgearbeitet; der vollständige Testlauf ist grün.
