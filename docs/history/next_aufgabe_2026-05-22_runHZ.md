# Nächste dokumentierte Aufgabe – Run HZ (2026-05-22)

## Aufgabe
Priorisierte nächste dokumentierte Aufgabe aus `docs/open_tasks.md` erneut ausführen (Folgelauf nach Run HY):

- `PYENV_VERSION=3.10.20 python -m pytest -q tests/test_satisfactory_regression_battery.py::test_satisfactory_successful_variants_reconversion_keeps_or_improves_quality`

## Ergebnis
- Exit-Code: `1`
- Laufzeit: `1.93s`
- Testresultat: `1 failed, 5 warnings`
- Log-Artefakt: `artifacts/converted_images/reports/TB_A3_xfail_probe_2026-05-22_runHZ.log`

## Einordnung
Der Lauf fällt nicht mehr als `xfail`, sondern bereits im Setup mit `FileNotFoundError` auf den fehlenden Pfad `artifacts/regression_baseline/satisfactory/images` aus. Damit liegt in dieser Umgebung aktuell ein Baseline-Artefakt-/Pfad-Blocker vor, der vor weiterer A3-Stabilisierung behoben werden muss.
