# Nächstes Arbeitspaket – Run KM (2026-05-24)

Dieses Arbeitspaket wurde als feste 3er-Kombination ausgeführt.

## 1) Nächste dokumentierte Aufgabe (TB-A3)
- Befehl:
  - `PYENV_VERSION=3.10.20 timeout 240 python -m pytest tests/test_satisfactory_regression_battery.py::test_satisfactory_successful_variants_reconversion_keeps_or_improves_quality -q`
- Ergebnis:
  - `1 skipped, 5 warnings`, Exit `0`.
- Log:
  - `artifacts/converted_images/reports/TB_A3_timeout_probe_2026-05-24_runKM.log`

## 2) Gekoppelte Plan-B-Aufgabe
- Befehl:
  - `PYTHONPATH=. python3 tools/plan_b_synthetic_probe.py "Bildbeschreibung: Kreis mit horizontalem Griff links und Beschriftung rF." --variant AC0060_S --output-dir artifacts/converted_images/reports`
- Ergebnis:
  - `status=ok`, `variant=AC0060_S`, Exit `0`.
- Log:
  - `artifacts/converted_images/reports/AC0060_S_planb_synthetic_2026-05-24_runKM.log`

## 3) Nächstes CSV-Bild
- Ausgeführter Einzellauf:
  - `PYTHONPATH=. timeout 240 python3 -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir artifacts/converted_images --start AC0060_S --end AC0060_S`
- Ergebnis:
  - Exit `0`; Konvertierung inkl. Plan-B-Vergleich durchgelaufen.
- Log:
  - `artifacts/converted_images/reports/AC0060_S_single_2026-05-24_runKM.log`

## Volltest (final)
- Befehl:
  - `PYENV_VERSION=3.10.20 timeout 300 python -m pytest -q -rs`
- Ergebnis:
  - `530 passed, 5 warnings`, Exit `0`.
- Log:
  - `artifacts/converted_images/reports/pytest_full_2026-05-24_runKM.log`

## Fazit
Das nächste dokumentierte Arbeitspaket wurde vollständig im geforderten Schema durchgeführt; TB-A3 und der finale Volltest bleiben grün.
