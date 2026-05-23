# Nächstes Arbeitspaket – Run IT (2026-05-23)

Dieses Arbeitspaket wurde als feste 3er-Kombination ausgeführt:
1. nächste dokumentierte Aufgabe,
2. genau eine gekoppelte Plan-B-Aufgabe,
3. nächstes Bild aus `artifacts/converted_images/reports/reports/summaries/not_satisfactory_converted_images.csv`.

## Vorab: Vollständiger Testlauf
- Befehl:
  - `PYENV_VERSION=3.10.20 PYTHONPATH=. pytest -q`
- Ergebnis:
  - `2 failed, 524 passed, 5 warnings`.
  - Fehlende Tests:
    - `tests/detailtests/test_cli_helpers.py::test_compat_cli_main_delegates_to_canonical_app`
    - `tests/detailtests/test_conversion_execution_helpers.py::test_convert_one_impl_prefers_new_vector_svg_over_existing_embedded_raster_even_when_delta2_is_worse`

## Vorab: Re-Konvertierungsversuch aller bisher erfolgreichen Varianten
- Baseline-Vorbereitung:
  - `PYENV_VERSION=3.10.20 PYTHONPATH=. python -m tools.manage_satisfactory_baseline --variants-file successed_conversions.txt --images-dir artifacts/images_to_convert --svgs-dir artifacts/converted_images/converted_svgs --baseline-dir artifacts/regression_baseline/satisfactory`
  - Ergebnis: `Prepared baseline pairs: 31`, `Missing pairs: 17`.
- Re-Konvertierungs-Test:
  - `PYENV_VERSION=3.10.20 PYTHONPATH=. timeout 600 pyenv exec python -m pytest tests/test_satisfactory_regression_battery.py::test_satisfactory_successful_variants_reconversion_keeps_or_improves_quality -q`
  - Ergebnis: `1 skipped, 5 warnings`, Exit `0`.

## 1) Nächste dokumentierte Aufgabe (TB-A3)
- Befehl:
  - `PYENV_VERSION=3.10.20 PYTHONPATH=. timeout 120 pyenv exec python -m pytest tests/test_satisfactory_regression_battery.py::test_satisfactory_successful_variants_reconversion_keeps_or_improves_quality -q`
- Ergebnis:
  - `1 skipped, 5 warnings` (Exit `0`).
- Log:
  - `artifacts/converted_images/reports/TB_A3_timeout_probe_2026-05-23_runIT.log`

## 2) Gekoppelte Plan-B-Aufgabe (`AC0030`)
- Befehl:
  - `PYTHONPATH=. python3 -m tools.plan_b_synthetic_probe "Bildbeschreibung: Rundes Verbotsschild mit diagonaler Markierung und kontrastreichem Hintergrund." --variant AC0030 --output-dir artifacts/converted_images/reports`
- Ergebnis:
  - Plan-B-Syntheseprobe erfolgreich (`status=ok`, Exit `0`).
- Log:
  - `artifacts/converted_images/reports/AC0030_planb_synthetic_2026-05-23_runIT.log`

## 3) Nächstes CSV-Bild
- Nächstes nicht als `in samples=yes` markiertes Bild vor dem Lauf: `AC0030`.
- Befehl:
  - `PYTHONPATH=. timeout 240 python3 -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir artifacts/converted_images --start AC0030 --end AC0030`
- Ergebnis:
  - Einzellauf mit Exit `0` (inkl. AC0030-Varianten im Bereichslauf).
  - CSV-Tracking aktualisiert: `AC0030` auf `in samples=yes` gesetzt.
- Log:
  - `artifacts/converted_images/reports/AC0030_single_2026-05-23_runIT.log`

## Testbatterie (nach Arbeitspaket)
- Befehl:
  - `PYENV_VERSION=3.10.20 PYTHONPATH=. pytest -q`
- Ergebnis:
  - Unverändert `2 failed, 524 passed, 5 warnings`.
- Log:
  - `artifacts/converted_images/reports/pytest_full_2026-05-23_runIT.log`

## Fazit
Die angeforderte Reihenfolge wurde vollständig durchgeführt: Volltest vorab, Re-Konvertierungsversuch der bisherigen erfolgreichen Varianten, vollständige 3er-Kombination des nächsten Arbeitspakets und abschließender Volltest.
