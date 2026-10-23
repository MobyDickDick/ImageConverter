# Native Strukturoperatoren: Entwicklungsnachweis

Basis `dd832bd22`, Branch `codex/search-structure-operators-isolated-2026-10-23`.
[Verhalten, Abnahme und Restumfang](../../../docs/next_arbeitspaket_2026-10-23_structure_operators.md).

Die acht vor der Runtime-Änderung festgelegten synthetischen Eingaben liegen
unter `input/`. `cli-before/` und `cli-after/` enthalten kompakte dauerhafte
Belege echter überwachter CLI-Versuche mit jeweils fünf Sekunden Bildbudget
und Seed 17: **0/8 vorher, 5/8 nachher**. Alle negativen Versuche bleiben im
Nenner. Das ist keine unabhängige reale Familienabnahme.

Jeder Bericht enthält die Runtime-Prüfsummen. Tatsächliche SVG-Ausgaben,
Workerlogs, Aufsichtsdateien, Ergebniszeilen und unabhängige Zugriffsbelege sind
erhalten. Die unabhängige Nachprüfung benötigt keine abgeleiteten PNG-Vergleiche:

```powershell
.venv/Scripts/python.exe -m tools.evaluate_structure_operators --inputs artifacts/evaluation/structure_operators_v1/input --output artifacts/evaluation/structure_operators_v1/cli-before --verify-only
.venv/Scripts/python.exe -m tools.evaluate_structure_operators --inputs artifacts/evaluation/structure_operators_v1/input --output artifacts/evaluation/structure_operators_v1/cli-after --verify-only
.venv/Scripts/python.exe -m tools.evaluate_structure_operators --inputs artifacts/evaluation/structure_operators_v1/input --output .tmp/structure-operators-repeat
.venv/Scripts/python.exe -m pytest tests/test_structure_search_operators.py tests/test_residual_scene_search.py tests/test_mixed_gradient_scene_runtime.py -q
```

`archive-preservation.json` belegt 379/379 Pixelprüfungen und 758 unveränderte
Prüfsummen gespeicherter Archivpaare. Es ist keine Archiv-Neukonvertierung.
`checks.json` fasst die abschließenden Testläufe und ihre Grenzen zusammen.
