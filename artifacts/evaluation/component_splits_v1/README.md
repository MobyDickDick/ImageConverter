# Komponentenaufteilung: synthetischer Entwicklungsnachweis

Basis `628da4bd0`, Branch `codex/search-structure-component-splits-2026-10-23`.
[Verhalten, Ergebnisse und Grenzen](../../../docs/next_arbeitspaket_2026-10-23_component_splits.md).

`input/` enthält die vor der Runtime-Änderung eingefrorenen 20 Eingaben.
`cli-before/` erreicht 8/20, `proof-cli/` erreicht 20/20 bei unveränderten
Objekt-, Relations-, Regions- und Pixelgates. Beide echten überwachten CLI-Läufe
verwenden fünf Sekunden pro Bild und Suchseed 17.

`new-input/` und `proof-new-cli/` enthalten zwölf weitere synthetische Fälle
mit Seed 918373: 12/12. Sie wurden nach dem ersten Code-Freeze erzeugt und
nach der letzten Speicherbegrenzung erneut geprüft. Keine reale Familienabnahme.

`plan-b-input/` enthält genau eine gekoppelte Plan-B-Vorlage mit 16 Varianten.
Der erste Entwicklungsversuch in `plan-b-cli/` scheitert bei 16/17 Fällen an
dem bislang nicht verarbeiteten Zusatz zum gesamten verschobenen/skalierten
Motiv. Nach Anschluss der vorhandenen geschlossenen Grammatik erreicht
`proof-plan-b/` 17/17; der negative Erstversuch bleibt erhalten.

`proof-residual/` wiederholt die neun bisherigen Restbildfälle mit 7/9.
Die beiden kontrastarmen Fehlversuche bleiben im Nenner. Die Eingaben dafür
liegen bereits unter `../residual_scene_v1/final-input/`.

Die Berichte enthalten Runtime-Prüfsummen; `checks.json` bindet die Endläufe
an denselben endgültigen Quellstand. **372/372 Tests** bestehen, einschließlich
aller **32 neuen Tests**; `tests-final.xml` und `tests-final.log` enthalten den
vollständigen gezielten Lauf. Gespeichert sind die tatsächlichen SVGs,
Ergebniszeilen, Workerlogs, Suchtelemetrie, Deadlineberichte und beide
Referenzzugriffsbelege. Doppelte Raster und abgeleitete Übersichten bleiben
lokal. Für unabhängige Nachprüfung reichen die versionierten Dateien:

```powershell
.venv/Scripts/python.exe -m tools.evaluate_component_splits --inputs artifacts/evaluation/component_splits_v1/input --output artifacts/evaluation/component_splits_v1/cli-before --verify-only
.venv/Scripts/python.exe -m tools.evaluate_component_splits --inputs artifacts/evaluation/component_splits_v1/input --output artifacts/evaluation/component_splits_v1/proof-cli --verify-only --require-all
.venv/Scripts/python.exe -m tools.evaluate_component_splits --inputs artifacts/evaluation/component_splits_v1/new-input --output artifacts/evaluation/component_splits_v1/proof-new-cli --verify-only --require-all
.venv/Scripts/python.exe -m tools.evaluate_component_splits --inputs artifacts/evaluation/component_splits_v1/plan-b-input --output artifacts/evaluation/component_splits_v1/proof-plan-b --verify-only --require-all
.venv/Scripts/python.exe -m tools.evaluate_residual_scene --inputs artifacts/evaluation/residual_scene_v1/final-input --output artifacts/evaluation/component_splits_v1/proof-residual --verify-only
```

Neue Wiederholung außerhalb der eingefrorenen Ordner:

```powershell
.venv/Scripts/python.exe -m tools.evaluate_component_splits --prepare .tmp/split-input --include-edits
.venv/Scripts/python.exe -m tools.evaluate_component_splits --inputs .tmp/split-input --output .tmp/split-cli --require-all
.venv/Scripts/python.exe -m pytest tests/test_component_splits.py tests/test_structure_search_operators.py tests/test_residual_scene_search.py tests/test_mixed_gradient_scene_runtime.py -q
```

`archive-preservation.json` belegt 379/379 absolute Pixelprüfungen und 758
unveränderte Prüfsummen gespeicherter Paare; es ist keine Archiv-Neukonvertierung.
Die vollständige historische Gesamtsuite wurde in diesem Teilpaket nicht
erneut ausgeführt. Ihre zuvor dokumentierten Zeitmessungsfehler werden dadurch
nicht als behoben beansprucht.
