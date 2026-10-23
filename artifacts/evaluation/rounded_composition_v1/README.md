# Gerundete Restbildkomposition: synthetischer Entwicklungsnachweis

Basis `985ee019c`, Branch `codex/search-structure-rounded-composition-2026-10-23`.
[Verhalten, Ursachenvergleich und Grenzen](../../../docs/next_arbeitspaket_2026-10-23_rounded_composition.md).

`development/` enthält zwölf vor der Runtime-Änderung gespeicherte Eingaben,
Beschreibungen, unabhängige native Objektmarkierungen und Prüfsummen.
`before/` erreicht 0/12, `final_cli/` mit neutralen Namen 12/12. Ein erster
positiver Entwicklungslauf in `after/` bleibt lokal; die versionierte finale
Gegenprobe verwendet die endgültige Runtime.

`additional/` enthält zwölf nach dem Runtime-Freeze erzeugte weitere Szenen
(Seed 918247), `additional_cli/` erreicht 12/12. `plan_b/` enthält genau eine
gekoppelte Vorlage samt 16 Größen-/Verschiebungsvarianten, `plan_b_cli/`
erreicht 17/17. Alle Szenen sind synthetisch, keine neue reale Familienabnahme.

Die Berichte enthalten sämtliche Runtime-Prüfsummen. Alle CLI-Läufe verwenden
fünf Sekunden je Bild und Suchseed 17. Die unabhängige Nachprüfung verlangt
native Objekte mit passender Geometrie einschließlich Eckradius, Objektregionen,
globale Qualität und leere Zugriffsprotokolle beider Referenzvektorwächter.
Die gespeicherten SVGs, Ergebniszeilen, Deadlineberichte und Workerlogs sind
vollständig erneut prüfbar; abgeleitete Raster/Übersichten bleiben lokal.

```powershell
.venv/Scripts/python.exe -m tools.evaluate_rounded_composition --inputs artifacts/evaluation/rounded_composition_v1/development --output artifacts/evaluation/rounded_composition_v1/before --verify-only
.venv/Scripts/python.exe -m tools.evaluate_rounded_composition --inputs artifacts/evaluation/rounded_composition_v1/development --output artifacts/evaluation/rounded_composition_v1/final_cli --verify-only --require-all
.venv/Scripts/python.exe -m tools.evaluate_rounded_composition --inputs artifacts/evaluation/rounded_composition_v1/additional --output artifacts/evaluation/rounded_composition_v1/additional_cli --verify-only --require-all
.venv/Scripts/python.exe -m tools.evaluate_rounded_composition --inputs artifacts/evaluation/rounded_composition_v1/plan_b --output artifacts/evaluation/rounded_composition_v1/plan_b_cli --verify-only --require-all
```

`existing_split_cli/` wiederholt die 20 bekannten Split-/Operatorfälle;
deren Eingaben liegen unter `../component_splits_v1/input/`. Die neun bekannten
Restbildfälle in `existing_residual_cli/` verwenden
`../residual_scene_v1/final-input/`. `checks.json` enthält Ergebnisse,
Runtime-Bindung und Abschlussprüfungen. `archive-preservation.json` belegt
379/379 Pixelprüfungen der gespeicherten Paare und 758 unveränderte Hashes;
es ist keine vollständige Archiv-Neukonvertierung.

Die vollständige Standardsuite besteht: **3.999 bestanden, 30 übersprungen,
kein Fehler** in 2.783,37 Sekunden. Die 34 neuen gezielten Tests sind enthalten.
Das vollständige Protokoll liegt unter `logs/pytest-full.log`. Syntax, CLI-Hilfe,
Runtime-ID-Nullprüfung und Whitespace-Prüfung mit bestehenden Windows-Zeilenenden
bestehen. Sämtliche CLI-Kohorten wurden außerdem aus einer separaten Kopie
der für Git ausgewählten Dateien unabhängig nachgeprüft.

Neue Wiederholung in einem frischen lokalen Ordner:

```powershell
.venv/Scripts/python.exe -m tools.evaluate_rounded_composition --prepare .tmp/rounded-input
.venv/Scripts/python.exe -m tools.evaluate_rounded_composition --inputs .tmp/rounded-input --output .tmp/rounded-cli --require-all
.venv/Scripts/python.exe -m pytest -q tests/test_rounded_composition.py
```
