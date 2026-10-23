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

Vollständiger isolierter Standardlauf: **3.931 bestanden, 30 übersprungen,
zwei fehlgeschlagen**, 70:38 Minuten. Alle 19 neuen Tests bestehen darin.
Die gezielte Szenengruppe besteht separat 78/78. Das vollständige Original-Log
steht in `full-suite.log`; die beiden unveränderten zeitabhängigen Fehler sind
unten getrennt untersucht. Die gezielten Wiederholungen ersetzen diese
Fehlschläge nicht.

`residual-repeat.json` dokumentiert die echte neue 7/9-CLI-Wiederholung. Die
sieben erfolgreichen SVGs sind bytegleich zu den bereits versionierten
Scheduler-Ausgaben, die im Bericht jeweils verlinkt sind.

`component-observation-base.json`, `component-observation-current.json` und die
zugehörige Probe untersuchen einen unveränderten, zeitabhängigen Bot-Test.
Die 200 Wiederholungen zeigen 3 Abweichungen mit dem ursprünglichen
`ImageSearch` und 0 mit dem neuen Stand. Das belegt eine schon vorhandene
Schwankung, keinen Komponenten- oder Qualitätsgewinn. Kandidaten und Budgets
unterscheiden sich in den gespeicherten negativen Beobachtungen. Das ganze
Komponentenmodul besteht separat 28/28; diese Wiederholung ersetzt den breiten
Lauf nicht. Der vollständige Abschlussstand steht in `checks.json`.

`neural-deadline/` enthält die zweite zeitabhängige Testauffälligkeit:
Das Zwei-Sekunden-Budget läuft im breiten Lauf vor dem Eintritt in die
Netzinferenz ab (2,016 Sekunden); die gezielte Wiederholung besteht.
Die gesicherte Zeitspur unterscheidet diesen Startabbruch von einer
tatsächlich betretenen blockierten Inferenz. Test- und Deadlinecode bleiben
unverändert; auch diese Wiederholung ersetzt keinen grünen breiten Erstlauf.
