# T6.10 Isolationslauf + gekoppelte Plan-B-Aufgabe (Run 08, 2026-05-16)

## Kontext

- Primäraufgabe: **T6.10** `test_validate_badge_logs_extent_bracketing_for_line_elements` erneut isoliert und timeout-gesichert ausführen.
- Gekoppelte Plan-B-Aufgabe: **T6-PB** historischer Einzeltest-Blocker als Kurzrepro.

## Ausführung

1. `PYENV_VERSION=3.10.20 timeout 180 python -m pytest tests/test_image_composite_converter.py::test_validate_badge_logs_extent_bracketing_for_line_elements -q`
2. `PYENV_VERSION=3.10.20 python -m pytest -q tests/detailtests/test_global_search_optimization_helpers.py::test_global_search_skips_deterministic_track_after_strong_stochastic_gain`

## Ergebnis

- **T6.10 (Run 08):** `1 passed` in `58.50s`, Exit `0`.  
  Log: `artifacts/converted_images/reports/t6_10_isolation_2026-05-16_run08.log`
- **T6-PB (Run 08):** `1 passed` in `0.14s`, Exit `0`.  
  Log: `artifacts/converted_images/reports/t6_planb_singletest_2026-05-16_run08.log`

## Bewertung ggü. Akzeptanzkriterium T6.10

- Das Kriterium `<= 35s` ist in diesem Lauf **nicht** erreicht (`58.50s`), jedoch blieb der Test stabil grün mit Exit `0`.
