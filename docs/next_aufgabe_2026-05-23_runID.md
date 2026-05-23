# Nächste dokumentierte Aufgabe – Run ID (2026-05-23)

## Ausgeführt
- Befehl:
  - `PYENV_VERSION=3.10.20 PYTHONPATH=. timeout 120 pyenv exec python -m pytest tests/test_satisfactory_regression_battery.py::test_satisfactory_successful_variants_reconversion_keeps_or_improves_quality -q`
- Ergebnis: `1 failed, 5 warnings`, Exit `1`.
- Log-Artefakt: `artifacts/converted_images/reports/TB_A3_timeout_probe_2026-05-23_runID.log`.

## Kurzfazit
Die nächste dokumentierte Aufgabe wurde erneut ausgeführt und bestätigt unverändert den bekannten Setup-Blocker: `FileNotFoundError` auf `artifacts/regression_baseline/satisfactory/images`.


## Folgeausführung – Run IE (2026-05-23)
- Befehl:
  - `PYENV_VERSION=3.10.20 PYTHONPATH=. timeout 120 pyenv exec python -m pytest tests/test_satisfactory_regression_battery.py::test_satisfactory_successful_variants_reconversion_keeps_or_improves_quality -q`
- Ergebnis: `1 failed, 5 warnings`, Exit `1`.
- Bestätigter Blocker: `FileNotFoundError` auf `artifacts/regression_baseline/satisfactory/images`.
- Log-Artefakt: `artifacts/converted_images/reports/TB_A3_timeout_probe_2026-05-23_runIE.log`.

## Volltestlauf – Run IE (2026-05-23)
- Befehl:
  - `PYENV_VERSION=3.10.20 PYTHONPATH=. timeout 300 pyenv exec python -m pytest -q`
- Ergebnis: Lauf endet ohne Endsummary im Timeout-Fenster (abgebrochener Fortschritt bis `91%`), damit **nicht erfolgreich abgeschlossen**.
- Beobachtung aus Fortschrittsausgabe: mindestens `11` Skip-Marker (`s`) im Laufprotokoll.
- Log-Artefakt: `artifacts/converted_images/reports/pytest_full_2026-05-23_runIE.log`.
