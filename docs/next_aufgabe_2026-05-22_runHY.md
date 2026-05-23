# Nächste dokumentierte Aufgabe – Run HY (2026-05-22)

## Aufgabe
Priorisierte nächste dokumentierte Aufgabe aus `docs/open_tasks.md` erneut ausführen:

- `PYENV_VERSION=3.10.20 python -m pytest -q tests/test_satisfactory_regression_battery.py::test_satisfactory_successful_variants_reconversion_keeps_or_improves_quality`

## Ergebnis
- Exit-Code: `1`
- Laufzeit: `2.79s`
- Testresultat: `1 failed, 5 warnings`
- Log-Artefakt: `artifacts/converted_images/reports/TB_A3_xfail_probe_2026-05-22_runHY.log`

## Einordnung
Der zuvor in Run HX erstmals grüne Lauf ist in Run HY nicht stabil reproduzierbar. Der Test bricht aktuell mit `FileNotFoundError` auf `artifacts/regression_baseline/satisfactory/images` ab. Damit bleibt die A3-Folgeaufgabe "stabil wiederholbar grün" offen und sollte mit einem Baseline-Pfad-Guard bzw. einem reproduzierbaren Setup-Schritt abgesichert werden.
