# Nächstes Arbeitspaket – Run IO (2026-05-23)

Dieses Arbeitspaket wurde wieder als feste 3er-Kombination ausgeführt:
1. nächste dokumentierte Aufgabe,
2. genau eine gekoppelte Plan-B-Aufgabe,
3. nächstes Bild aus `artifacts/converted_images/reports/reports/summaries/not_satisfactory_converted_images.csv`.

## 1) Nächste dokumentierte Aufgabe (TB-A3)
- Befehl:
  - `PYENV_VERSION=3.10.20 pyenv exec python -m tools.manage_satisfactory_baseline --variants-file successed_conversions.txt --images-dir artifacts/images_to_convert --svgs-dir artifacts/converted_images/converted_svgs --baseline-dir artifacts/regression_baseline/satisfactory`
  - `PYENV_VERSION=3.10.20 PYTHONPATH=. timeout 300 pyenv exec python -m pytest tests/test_satisfactory_regression_battery.py::test_satisfactory_successful_variants_reconversion_keeps_or_improves_quality -q`
- Ergebnis:
  - Baseline vorbereitet (`Prepared baseline pairs: 25`).
  - Priorisierter TB-A3-Lauf erneut grün: `1 passed, 5 warnings`, Exit `0`.
- Logs:
  - `artifacts/converted_images/reports/TB_A3_baseline_prepare_2026-05-23_runIO.log`
  - `artifacts/converted_images/reports/TB_A3_timeout_probe_2026-05-23_runIO.log`

## 2) Gekoppelte Plan-B-Aufgabe
- Befehl:
  - `PYTHONPATH=. python3 tools/plan_b_synthetic_probe.py "Bildbeschreibung: Kreis mit horizontalem Griff links und Beschriftung rF." --variant AC0024 --output-dir artifacts/converted_images/reports`
- Ergebnis:
  - `status=ok`, Exit `0`.
- Log:
  - `artifacts/converted_images/reports/AC0024_planb_synthetic_2026-05-23_runIO.log`

## 3) Nächstes CSV-Bild
- Nächstes nicht als `in samples=yes` markiertes Bild vor dem Lauf: `AC0024`.
- Befehl:
  - `PYTHONPATH=. timeout 240 python3 -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir artifacts/converted_images --start AC0024 --end AC0024`
- Ergebnis:
  - Einzellauf `AC0024` mit Exit `0`.
  - CSV-Tracking aktualisiert: `AC0024` auf `in samples=yes` gesetzt.
- Log:
  - `artifacts/converted_images/reports/AC0024_single_2026-05-23_runIO.log`

## Fazit
Das nächste Arbeitspaket wurde vollständig in der definierten 3er-Kombination ausgeführt. Der TB-A3-Lauf bleibt nach direktem Re-Run stabil grün, die gekoppelte Plan-B-Aufgabe ist erfolgreich, und das nächste offene CSV-Bild wurde bearbeitet und nachgeführt.
