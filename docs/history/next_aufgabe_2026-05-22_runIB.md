# Nächste dokumentierte Aufgabe – Run IB (2026-05-22)

## Aufgabe
Priorisierte nächste dokumentierte Aufgabe aus `docs/open_tasks.md` erneut ausführen (Folgelauf nach Run IA):

- `PYENV_VERSION=3.10.20 python -m pytest -q tests/test_satisfactory_regression_battery.py::test_satisfactory_successful_variants_reconversion_keeps_or_improves_quality`

## Ergebnis
- Exit-Code: `1`
- Testresultat: `1 failed, 5 warnings`
- Log-Artefakt: `artifacts/converted_images/reports/TB_A3_xfail_probe_2026-05-22_runIB.log`

## Einordnung
Der Folgelauf bestätigt den bereits dokumentierten Setup-Blocker unverändert: `FileNotFoundError` auf `artifacts/regression_baseline/satisfactory/images`. Die A3-Stabilisierung bleibt damit bis zur Wiederherstellung der Satisfactory-Baseline-Artefakte blockiert.
