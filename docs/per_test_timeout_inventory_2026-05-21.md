# _PerTestTimeout Inventar (Stand 2026-05-21)

Quelle:
- `tests/conftest.py` (_PerTestTimeout Hook, 30s Grenze)
- `docs/timeout_tasks_2026-05-20.md`
- `timeout 360 python -m pytest -q -rxX` (Exit 124)

## Aktuelle Timeout-Folgeaufgaben (1:1)

1. `tests/test_conversion_regression_smoke.py::test_ac08_regression_smoke_run_creates_expected_outputs`
   - Akzeptanz: Lauf ohne Skip/Timeout und stabile erwartete Smoke-Ausgaben.
2. `tests/test_satisfactory_regression_battery.py::test_satisfactory_successful_variants_reconversion_keeps_or_improves_quality`
   - Akzeptanz: Laufzeit <30s unter Python 3.10.20 im `core-green` Profil.

## Regel

Timeout-Fälle bleiben als offene Qualitätsaufgaben geführt, bis die 30s-Grenze stabil unterschritten wird und der Test wieder regulär im Kernprofil läuft.
