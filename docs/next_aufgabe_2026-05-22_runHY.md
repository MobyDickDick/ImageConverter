# Nächste dokumentierte Aufgabe – Run HY (2026-05-22)

## Aufgabe
Priorisierte nächste dokumentierte Aufgabe aus `docs/open_tasks.md` erneut ausführen (Stabilisierung nach Run HX):

- `PYENV_VERSION=3.10.20 python -m pytest -q tests/test_satisfactory_regression_battery.py::test_satisfactory_successful_variants_reconversion_keeps_or_improves_quality`

## Ergebnis
- Exit-Code: `0`
- Laufzeit: `186.69s`
- Testresultat: `1 xfailed, 5 warnings`
- Log-Artefakt: `artifacts/converted_images/reports/TB_A3_xfail_probe_2026-05-22_runHY.log`

## Einordnung
Der in Run HX einmalig grüne A3-Kandidat ist im direkten Wiederholungslauf wieder als `xfail` zurückgefallen. Damit bleibt A3 offen; die Schwankung bestätigt, dass der Fall derzeit nicht stabil als „wirklich grün“ gewertet werden kann.
