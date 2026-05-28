# Nächstes Arbeitspaket – Run LD (2026-05-27)

Dieses Arbeitspaket wurde im festen 3er-Schema inklusive finalem Volltest ausgeführt.

## 1) Nächste dokumentierte Aufgabe (TB-A3)
- Befehl:
  - `PYENV_VERSION=3.10.20 PYTHONPATH=vendor/linux-py310/site-packages:. timeout 240 python -m pytest tests/test_satisfactory_regression_battery.py::test_satisfactory_successful_variants_reconversion_keeps_or_improves_quality -q`
- Ergebnis:
  - Exit `0`
  - `1 skipped, 5 warnings in 2.96s`
- Log:
  - `artifacts/converted_images/reports/TB_A3_timeout_probe_2026-05-27_runLD.log`

## 2) Gekoppelte Plan-B-Aufgabe
- Befehl:
  - `PYENV_VERSION=3.10.20 PYTHONPATH=vendor/linux-py310/site-packages:. python tools/plan_b_roundtrip.py artifacts/images_to_convert/samples/AC0153_L.svg --output-dir artifacts/converted_images/reports`
- Ergebnis:
  - Exit `0`
  - `variant=AC0153_L`, `delta2_output_vs_sample=0.000000`
- Log:
  - `artifacts/converted_images/reports/AC0153_L_planb_roundtrip_2026-05-27_runLD.log`

## 3) Nächstes Bild / Einzellauf
- Befehl:
  - `PYENV_VERSION=3.10.20 PYTHONPATH=vendor/linux-py310/site-packages:. timeout 240 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir artifacts/converted_images --start AC0100_S --end AC0100_S`
- Ergebnis:
  - Exit `0`
  - Einzellauf abgeschlossen; Übersichts-Kacheln aktualisiert.
- Log:
  - `artifacts/converted_images/reports/AC0100_S_single_2026-05-27_runLD.log`

## Volltest (final)
- Befehl:
  - `PYENV_VERSION=3.10.20 PYTHONPATH=vendor/linux-py310/site-packages:. timeout 300 python -m pytest -q -rs`
- Ergebnis:
  - Exit `0`
  - `547 passed, 5 warnings in 7.62s`
- Log:
  - `artifacts/converted_images/reports/pytest_full_2026-05-27_runLD.log`

## Fazit
Das nächste dokumentierte Arbeitspaket wurde vollständig im geforderten Schema durchgeführt; TB-A3, gekoppelte Plan-B-Aufgabe, Einzellauf und finaler Volltest sind grün.
