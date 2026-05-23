# Nächste dokumentierte Aufgabe – Run IG (2026-05-23)

## Aufgabe
Priorisierte nächste dokumentierte Aufgabe aus `docs/open_tasks.md` erneut ausführen:

- `PYENV_VERSION=3.10.20 PYTHONPATH=. timeout 120 pyenv exec python -m pytest tests/test_satisfactory_regression_battery.py::test_satisfactory_successful_variants_reconversion_keeps_or_improves_quality -q`

## Ergebnis
- Exit-Code: `1`
- Testresultat: `1 failed, 5 warnings`
- Bestätigter Blocker: `FileNotFoundError` auf `artifacts/regression_baseline/satisfactory/images`
- Log-Artefakt: `artifacts/converted_images/reports/TB_A3_timeout_probe_2026-05-23_runIG.log`

## Volltestlauf
- Befehl:
  - `PYENV_VERSION=3.10.20 PYTHONPATH=. timeout 300 pyenv exec python -m pytest -q`
- Ergebnis: Lauf endet durch Timeout (`exit 124`) ohne Endsummary.
- Beobachtung: Fortschrittsanzeige bis `~91%` mit mehreren `skip`-Markern, danach Timeout.
- Log-Artefakt: `artifacts/converted_images/reports/pytest_full_2026-05-23_runIG.log`
