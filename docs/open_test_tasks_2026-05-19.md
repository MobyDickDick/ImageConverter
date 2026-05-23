# Offene Test-Aufgaben (Stand 2026-05-19)

Ziel: Einen stabilen, schnell laufenden Testblock grün halten und die aktuell bekannten Problemfälle separat nachverfolgen.

## Stabil laufender Testblock
Folgende Tests laufen aktuell grün (unter Python 3.10.20):

```bash
PYENV_VERSION=3.10.20 pytest -q \
  tests/detailtests/test_conversion_execution_helpers.py \
  tests/detailtests/test_iteration_setup_helpers.py \
  tests/detailtests/test_quality_config_helpers.py
```

Ergebnis: `17 passed, 3 xfailed`.

## Als Aufgaben extrahierte (xfail) Problemfälle

### TASK-1: Failed-SVG bei `semantic_mismatch` wird nicht geschrieben ✅ (2026-05-21 erledigt)
- Test: `test_convert_one_impl_semantic_mismatch_is_reported_as_failure`
- Datei: `tests/detailtests/test_conversion_execution_helpers.py`
- Erwartung: `Failed_<name>.svg` wird erzeugt und enthält das eingebettete Fallback-SVG.

### TASK-2: Failed-SVG bei unbekanntem/non-success Status wird nicht geschrieben ✅ (2026-05-21 erledigt)
- Test: `test_convert_one_impl_unknown_status_is_recorded_as_failure`
- Datei: `tests/detailtests/test_conversion_execution_helpers.py`
- Erwartung: `Failed_<name>.svg` wird erzeugt und enthält das eingebettete Fallback-SVG.

### TASK-3: Failed-SVG bei trivialem Placeholder wird nicht geschrieben ✅ (2026-05-21 erledigt)
- Test: `test_convert_one_impl_trivial_placeholder_svg_is_marked_failed`
- Datei: `tests/detailtests/test_conversion_execution_helpers.py`
- Erwartung: `Failed_<name>.svg` existiert nach Verarbeitung.


### TASK-4: Satisfactory-Baseline-Regressionstest scheitert ohne Testdaten-Setup ❌ (neu 2026-05-23)
- Test: `tests/test_satisfactory_regression_battery.py::test_satisfactory_successful_variants_reconversion_keeps_or_improves_quality`
- Beobachtung: `FileNotFoundError` auf `artifacts/regression_baseline/satisfactory/images`.
- Erwartung: Test soll entweder reproduzierbar die benötigte Baseline vorbereiten oder bei fehlenden Artefakten sauber `skippen` statt als Hard-Fail zu enden.
- Repro:
  - `PYENV_VERSION=3.10.20 PYTHONPATH=. timeout 120 pyenv exec python -m pytest tests/test_satisfactory_regression_battery.py::test_satisfactory_successful_variants_reconversion_keeps_or_improves_quality -q`
- Artefakt: `artifacts/converted_images/reports/TB_A3_timeout_probe_2026-05-23_runID.log`.


### TASK-5: Global-Search-Kleingewinn-Repro ist flaky/unter Zielschwelle ❌ (neu 2026-05-23)
- Test: `tests/detailtests/test_global_search_optimization_helpers.py::test_global_search_does_not_count_small_relevant_gain_as_no_improvement`
- Beobachtung: Assertion `float(params["arm_x1"]) >= 1.10` schlägt fehl (`1.052784303601394`).
- Erwartung: Optimierungslogik soll bei kleinem relevantem Gewinn konsistent über die Zielschwelle verbessern oder der Test muss auf stabile, deterministische Akzeptanzkriterien umgestellt werden.
- Repro:
  - `PYENV_VERSION=3.10.20 PYTHONPATH=. pyenv exec pytest -q --maxfail=1`
- Artefakt: `artifacts/converted_images/reports/pytest_full_maxfail1_2026-05-23_runID.log`.

## Empfohlener Abarbeitungsmodus
1. Produktionslogik für File-Emission in `convertOneImpl` vereinheitlichen (ein zentraler Write/Move-Pfad für Failed-SVG).
2. Jeden Task einzeln fixen und mit `-k` gezielt validieren.
3. Nach jedem Fix `xfail` entfernen und Test auf normal `pass` umstellen.
4. Danach wieder größeren Block laufen lassen.
