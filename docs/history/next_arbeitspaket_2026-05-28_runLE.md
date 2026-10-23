# Nächstes Arbeitspaket – Run LE (2026-05-28)

Dieses Arbeitspaket wurde im festen 3er-Schema inklusive finalem Volltest ausgeführt.

## 1) Nächste dokumentierte Aufgabe (TB-A3)
- Befehl:
  - `PYENV_VERSION=3.10.20 PYTHONPATH=vendor/linux-py310/site-packages:. timeout 240 python -m pytest tests/test_satisfactory_regression_battery.py::test_satisfactory_successful_variants_reconversion_keeps_or_improves_quality -q`
- Ergebnis:
  - Exit `0`
  - `1 skipped, 5 warnings in 3.73s`
- Log:
  - `artifacts/converted_images/reports/TB_A3_timeout_probe_2026-05-28_runLE.log`

## 2) Gekoppelte Plan-B-Aufgabe
- Befehl:
  - `PYENV_VERSION=3.10.20 PYTHONPATH=vendor/linux-py310/site-packages:. python tools/plan_b_roundtrip.py artifacts/images_to_convert/samples/AC0223_L.svg --output-dir artifacts/converted_images/reports`
- Ergebnis:
  - Exit `0`
  - `variant=AC0223_L`, `delta2_output_vs_sample=431.700883`
- Log:
  - `artifacts/converted_images/reports/AC0223_L_planb_roundtrip_2026-05-28_runLE.log`

## 3) Nächstes Bild / Einzellauf
- Befehl:
  - `PYENV_VERSION=3.10.20 PYTHONPATH=vendor/linux-py310/site-packages:. timeout 240 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir artifacts/converted_images --start AC0110_L --end AC0110_L`
- Ergebnis:
  - Exit `0`
  - Einzellauf abgeschlossen; Übersichts-Kacheln aktualisiert.
- Log:
  - `artifacts/converted_images/reports/AC0110_L_single_2026-05-28_runLE.log`

## Volltest (final)
- Befehl:
  - `PYENV_VERSION=3.10.20 PYTHONPATH=vendor/linux-py310/site-packages:. timeout 300 python -m pytest -q -rs`
- Ergebnis:
  - Exit `0`
  - `547 passed, 5 warnings in 9.17s`
- Log:
  - `artifacts/converted_images/reports/pytest_full_2026-05-28_runLE.log`

## Fazit
Das nächste dokumentierte Arbeitspaket wurde vollständig im geforderten Schema durchgeführt; TB-A3, gekoppelte Plan-B-Aufgabe, Einzellauf und finaler Volltest sind grün.
