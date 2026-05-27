# Nächstes Arbeitspaket – Run LB (2026-05-27)

Dieses Arbeitspaket wurde im festen 3er-Schema inklusive finalem Volltest ausgeführt.

## 1) Nächste dokumentierte Aufgabe (TB-A3)
- Befehl:
  - `PYENV_VERSION=3.10.20 PYTHONPATH=vendor/linux-py310/site-packages:. timeout 240 python -m pytest tests/test_satisfactory_regression_battery.py::test_satisfactory_successful_variants_reconversion_keeps_or_improves_quality -q`
- Ergebnis:
  - Exit `0`
  - `1 skipped, 5 warnings in 0.57s`
- Log:
  - `artifacts/converted_images/reports/TB_A3_timeout_probe_2026-05-27_runLB.log`

## 2) Gekoppelte Plan-B-Aufgabe
- Befehl:
  - `PYENV_VERSION=3.10.20 PYTHONPATH=vendor/linux-py310/site-packages:. python tools/plan_b_roundtrip.py artifacts/images_to_convert/samples/AC0130_L.svg --output-dir artifacts/converted_images/reports`
- Ergebnis:
  - Exit `0`
  - `variant=AC0130_L`, `delta2_output_vs_sample=141816.007732`
- Log:
  - `artifacts/converted_images/reports/AC0130_L_planb_roundtrip_2026-05-27_runLB.log`

## 3) Nächstes Bild / Einzellauf
- Befehl:
  - `PYENV_VERSION=3.10.20 PYTHONPATH=vendor/linux-py310/site-packages:. timeout 240 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir artifacts/converted_images --start AC0100_L --end AC0100_L`
- Ergebnis:
  - Exit `0`
  - Einzellauf abgeschlossen; Übersichts-Kacheln aktualisiert.
- Log:
  - `artifacts/converted_images/reports/AC0100_L_single_2026-05-27_runLB.log`

## Volltest (final)
- Befehl:
  - `PYENV_VERSION=3.10.20 PYTHONPATH=vendor/linux-py310/site-packages:. timeout 300 python -m pytest -q -rs`
- Ergebnis:
  - Exit `0`
  - `543 passed, 5 warnings in 5.61s`
- Log:
  - `artifacts/converted_images/reports/pytest_full_2026-05-27_runLB.log`

## Zusatzfix aus Testlauf
- `runMainImpl` greift bei `debug_jpeg_load` jetzt robust per `getattr(..., False)` zu, damit bestehende Tests mit abgespeckten `Namespace`-Fixtures nicht mit `AttributeError` abbrechen.
- Subprozess-Timeout-Defaulttests ergänzen den `PYTHONPATH` um das vendorte `site-packages`-Verzeichnis, sodass `src.imageCompositeConverter` in isolierten Python-Subprozessen reproduzierbar importierbar bleibt.
