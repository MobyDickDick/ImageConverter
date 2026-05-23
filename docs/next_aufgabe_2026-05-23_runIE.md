# Nächste dokumentierte Aufgabe – Run IE (2026-05-23)

## Ausgeführt
- Befehl:
  - `PYENV_VERSION=3.10.20 PYTHONPATH=. timeout 120 pyenv exec python -m pytest tests/test_satisfactory_regression_battery.py::test_satisfactory_successful_variants_reconversion_keeps_or_improves_quality -q`
- Ergebnis: `1 failed, 5 warnings`, Exit `1`.
- Beobachteter Blocker: `FileNotFoundError` auf `artifacts/regression_baseline/satisfactory/images`.

## Zusätzlicher Volltestlauf
- Befehl:
  - `PYENV_VERSION=3.10.20 PYTHONPATH=. timeout 300 pyenv exec python -m pytest -q`
- Ergebnis: Exit `124` (Timeout), kein finales `pytest`-Summary.
- Befund: Mindestens ein weiterer Fail vor Timeout sichtbar (`...F...` im Fortschrittsbalken), daher aktuell kein durchgehend grüner Volltestlauf.

## Kurzfazit
Die nächste dokumentierte Aufgabe wurde erneut ausgeführt und bestätigt unverändert den bekannten Setup-Blocker. Der Volltestlauf bleibt zusätzlich zeitkritisch und erreicht innerhalb von 300s kein Endsummary.


## Folgeausführung – Run IJ (2026-05-23)
- Befehl:
  - `PYENV_VERSION=3.10.20 PYTHONPATH=. timeout 120 pyenv exec python -m pytest tests/test_satisfactory_regression_battery.py::test_satisfactory_successful_variants_reconversion_keeps_or_improves_quality -q`
- Ergebnis: `1 failed, 5 warnings`, Exit `1`.
- Bestätigter Blocker: `FileNotFoundError` auf `artifacts/regression_baseline/satisfactory/images`.
- Log-Artefakt: `artifacts/converted_images/reports/TB_A3_timeout_probe_2026-05-23_runIJ.log`.

## Volltestlauf – Run IJ (2026-05-23)
- Befehl:
  - `PYENV_VERSION=3.10.20 PYTHONPATH=. timeout 300 pyenv exec python -m pytest -q -rs`
- Ergebnis: Lauf erneut ohne finales Summary innerhalb des 300s-Fensters (Fortschritt bis `91%`, danach kein Abschluss im Zeitfenster).
- Sichtbare Skip-Marker im Fortschritt: mindestens `11` (`s`).
- Log-Artefakt: `artifacts/converted_images/reports/pytest_full_2026-05-23_runIJ.log`.

## Blockierende Tests (Collect-only, Run IJ)
- Befehl:
  - `PYENV_VERSION=3.10.20 PYTHONPATH=. pyenv exec python -m pytest --collect-only -q -m blocking_conversion`
- Ergebnis: `20/867 tests collected (847 deselected)`.
- Log-Artefakt: `artifacts/converted_images/reports/blocking_collect_2026-05-23_runIJ.log`.

## Folgeausführung – Run IK (2026-05-23)
- Befehl:
  - `PYENV_VERSION=3.10.20 PYTHONPATH=. timeout 120 pyenv exec python -m pytest tests/test_satisfactory_regression_battery.py::test_satisfactory_successful_variants_reconversion_keeps_or_improves_quality -q`
- Ergebnis: `1 failed, 5 warnings`, fachlich Exit `1` (Fehlschlag reproduziert).
- Bestätigter Blocker: `FileNotFoundError` auf `artifacts/regression_baseline/satisfactory/images`.
- Log-Artefakt: `artifacts/converted_images/reports/TB_A3_timeout_probe_2026-05-23_runIK.log`.

## Volltestlauf – Run IK (2026-05-23)
- Befehl:
  - `PYENV_VERSION=3.10.20 PYTHONPATH=. timeout 300 pyenv exec python -m pytest -q -rs`
- Ergebnis: Exit `124` (Timeout) ohne finales `pytest`-Summary.
- Befund: Fortschritt erneut bis mindestens `91%`, weiterhin nicht vollständig grün im Zeitfenster.
- Log-Artefakt: `artifacts/converted_images/reports/pytest_full_2026-05-23_runIK.log`.

## Folgeausführung – Run IL (2026-05-23)
- Befehl:
  - `PYENV_VERSION=3.10.20 PYTHONPATH=. timeout 120 pyenv exec python -m pytest tests/test_satisfactory_regression_battery.py::test_satisfactory_successful_variants_reconversion_keeps_or_improves_quality -q`
- Ergebnis: `1 failed, 5 warnings` (Fehlschlag reproduziert).
- Bestätigter Blocker: `FileNotFoundError` auf `artifacts/regression_baseline/satisfactory/images`.
- Log-Artefakt: `artifacts/converted_images/reports/TB_A3_timeout_probe_2026-05-23_runIL.log`.

## Volltestlauf – Run IL (2026-05-23)
- Befehl:
  - `PYENV_VERSION=3.10.20 PYTHONPATH=. timeout 300 pyenv exec python -m pytest -q -rs`
- Ergebnis: Lauf diesmal mit finalem Summary abgeschlossen; `1 failed, 856 passed, 10 skipped, 5 warnings`.
- Befund: Der verbleibende Fail ist weiterhin `tests/test_satisfactory_regression_battery.py::test_satisfactory_successful_variants_reconversion_keeps_or_improves_quality` (`FileNotFoundError` auf Baseline-Images).
- Log-Artefakt: `artifacts/converted_images/reports/pytest_full_2026-05-23_runIL.log`.

## Folgeausführung – Run IM (2026-05-23)
- Befehl:
  - `PYENV_VERSION=3.10.20 PYTHONPATH=. timeout 120 pyenv exec python -m pytest tests/test_satisfactory_regression_battery.py::test_satisfactory_successful_variants_reconversion_keeps_or_improves_quality -q`
- Ergebnis: `1 failed, 5 warnings`, Exit `1`.
- Bestätigter Blocker: `FileNotFoundError` auf `artifacts/regression_baseline/satisfactory/images`.
- Log-Artefakt: `artifacts/converted_images/reports/TB_A3_timeout_probe_2026-05-23_runIM.log`.

## Volltestlauf – Run IM (2026-05-23)
- Befehl:
  - `PYENV_VERSION=3.10.20 PYTHONPATH=. timeout 300 pyenv exec python -m pytest -q -rs`
- Ergebnis: Exit `1`; im 300s-Fenster wurde kein finales `pytest`-Summary in das Log geschrieben.
- Befund: Fortschritt bis mindestens `91%` mit sichtbarem `F` kurz vor Laufende.
- Log-Artefakt: `artifacts/converted_images/reports/pytest_full_2026-05-23_runIM.log`.
