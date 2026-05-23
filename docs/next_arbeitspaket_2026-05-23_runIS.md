# Nächstes Arbeitspaket – Run IS (2026-05-23)

Dieses Arbeitspaket wurde als feste 3er-Kombination ausgeführt:
1. nächste dokumentierte Aufgabe,
2. genau eine gekoppelte Plan-B-Aufgabe,
3. nächstes Bild aus `artifacts/converted_images/reports/reports/summaries/not_satisfactory_converted_images.csv`.

## 1) Nächste dokumentierte Aufgabe (TB-A3)
- Befehle:
  - `PYENV_VERSION=3.10.20 pyenv exec python -m tools.manage_satisfactory_baseline --variants-file successed_conversions.txt --images-dir artifacts/images_to_convert --svgs-dir artifacts/converted_images/converted_svgs --baseline-dir artifacts/regression_baseline/satisfactory`
  - `PYENV_VERSION=3.10.20 PYTHONPATH=. timeout 300 pyenv exec python -m pytest tests/test_satisfactory_regression_battery.py::test_satisfactory_successful_variants_reconversion_keeps_or_improves_quality -q`
- Ergebnis:
  - Baseline vorbereitet (`Prepared baseline pairs: 31`).
  - TB-A3-Lauf reproduzierbar `skipped` (`1 skipped, 5 warnings`, Exit `0`).
- Logs:
  - `artifacts/converted_images/reports/TB_A3_baseline_prepare_2026-05-23_runIS.log`
  - `artifacts/converted_images/reports/TB_A3_timeout_probe_2026-05-23_runIS.log`

## 2) Gekoppelte Plan-B-Aufgabe (`AC0026`)
- Befehl:
  - `PYTHONPATH=. python3 -m tools.plan_b_synthetic_probe "Bildbeschreibung: Kreisförmiges Schild mit mittigem Symbol und kurzer horizontaler Markierung." --variant AC0026 --output-dir artifacts/converted_images/reports`
- Ergebnis:
  - Plan-B-Syntheseprobe erfolgreich ausgeführt (`status=ok`, Exit `0`).
- Log:
  - `artifacts/converted_images/reports/AC0026_planb_synthetic_2026-05-23_runIS.log`

## 3) Nächstes CSV-Bild
- Nächstes nicht als `in samples=yes` markiertes Bild vor dem Lauf: `AC0026`.
- Befehl:
  - `PYTHONPATH=. timeout 240 python3 -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir artifacts/converted_images --start AC0026 --end AC0026`
- Ergebnis:
  - Einzellauf `AC0026` mit Exit `0`.
  - CSV-Tracking aktualisiert: `AC0026` auf `in samples=yes` gesetzt.
- Log:
  - `artifacts/converted_images/reports/AC0026_single_2026-05-23_runIS.log`

## Testbatterie (nachgeführt)
- Befehl:
  - `PYENV_VERSION=3.10.20 pytest -q tests/detailtests/test_conversion_execution_helpers.py tests/detailtests/test_iteration_setup_helpers.py tests/detailtests/test_quality_config_helpers.py`
- Ergebnis:
  - `20 passed`, Exit `0`.
- Log:
  - `artifacts/converted_images/reports/test_battery_2026-05-23_runIS.log`

## Fazit
Das nächste Arbeitspaket wurde erneut in der geforderten 3er-Kombination abgeschlossen und mit einer grünen Detailtest-Batterie abgesichert.
