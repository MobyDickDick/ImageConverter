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

### TASK-1: Failed-SVG bei `semantic_mismatch` wird nicht geschrieben
- Test: `test_convert_one_impl_semantic_mismatch_is_reported_as_failure`
- Datei: `tests/detailtests/test_conversion_execution_helpers.py`
- Erwartung: `Failed_<name>.svg` wird erzeugt und enthält das eingebettete Fallback-SVG.

### TASK-2: Failed-SVG bei unbekanntem/non-success Status wird nicht geschrieben
- Test: `test_convert_one_impl_unknown_status_is_recorded_as_failure`
- Datei: `tests/detailtests/test_conversion_execution_helpers.py`
- Erwartung: `Failed_<name>.svg` wird erzeugt und enthält das eingebettete Fallback-SVG.

### TASK-3: Failed-SVG bei trivialem Placeholder wird nicht geschrieben
- Test: `test_convert_one_impl_trivial_placeholder_svg_is_marked_failed`
- Datei: `tests/detailtests/test_conversion_execution_helpers.py`
- Erwartung: `Failed_<name>.svg` existiert nach Verarbeitung.

## Empfohlener Abarbeitungsmodus
1. Produktionslogik für File-Emission in `convertOneImpl` vereinheitlichen (ein zentraler Write/Move-Pfad für Failed-SVG).
2. Jeden Task einzeln fixen und mit `-k` gezielt validieren.
3. Nach jedem Fix `xfail` entfernen und Test auf normal `pass` umstellen.
4. Danach wieder größeren Block laufen lassen.
