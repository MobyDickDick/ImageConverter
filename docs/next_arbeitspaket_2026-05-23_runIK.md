# Nächstes Arbeitspaket – Run IK (2026-05-23)

## Definition
Das **nächste Arbeitspaket** bleibt als feste Kombination aus:
1. nächster dokumentierter Aufgabe,
2. genau einer gekoppelten Plan-B-Aufgabe,
3. nächstem Bild aus `artifacts/converted_images/reports/reports/summaries/not_satisfactory_converted_images.csv`.

## 1) Nächste dokumentierte Aufgabe
- Befehl:
  - `PYENV_VERSION=3.10.20 PYTHONPATH=. timeout 120 pyenv exec python -m pytest tests/test_satisfactory_regression_battery.py::test_satisfactory_successful_variants_reconversion_keeps_or_improves_quality -q`
- Ergebnis: `1 failed, 5 warnings`, Exit `1`.
- Bestätigter Blocker: `FileNotFoundError` auf `artifacts/regression_baseline/satisfactory/images`.
- Log: `artifacts/converted_images/reports/TB_A3_timeout_probe_2026-05-23_runIK.log`

## 2) Gekoppelte Plan-B-Aufgabe
- Befehl:
  - `PYTHONPATH=. python3 tools/plan_b_synthetic_probe.py "Bildbeschreibung: Kreis mit horizontalem Griff links und Beschriftung rF." --variant AC0030_M --output-dir artifacts/converted_images/reports`
- Ergebnis: `status=ok`, Exit `0`.
- Log: `artifacts/converted_images/reports/AC0030_M_planb_synthetic_2026-05-23_runIK.log`

## 3) Nächstes CSV-Bild
- Quelle: `artifacts/converted_images/reports/reports/summaries/not_satisfactory_converted_images.csv`
- Nächster Eintrag nach zuletzt dokumentiertem `AC0030_S`: `AC0030_M`
- Bearbeitung:
  - `PYTHONPATH=. timeout 240 python3 -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir artifacts/converted_images --start AC0030_M --end AC0030_M`
- Ergebnis: Exit `0`.
- Log: `artifacts/converted_images/reports/AC0030_M_single_2026-05-23_runIK.log`

## Testbatterie (nachgeführt)
- Befehl:
  - `PYENV_VERSION=3.10.20 pytest -q tests/detailtests/test_conversion_execution_helpers.py tests/detailtests/test_iteration_setup_helpers.py tests/detailtests/test_quality_config_helpers.py`
- Ergebnis: `20 passed`, Exit `0`.
- Log: `artifacts/converted_images/reports/test_battery_2026-05-23_runIK.log`

## Kurzfazit
Das Arbeitspaket wurde in der definierten 3er-Kombination ausgeführt. Die gekoppelte Plan-B-Aufgabe und die Testbatterie sind grün, während die priorisierte dokumentierte Aufgabe weiterhin am bekannten Baseline-Pfad-Blocker scheitert.
