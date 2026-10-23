# Runde Rechteckkinder mit hellen Konturen: synthetische Entwicklung

Ausgangsstand `00dfb2cc7`, Branch
`codex/search-structure-rounded-outlines-2026-10-23`.
[Aufgabe, Umsetzung, verworfene Ansätze und Grenzen](../../../docs/next_arbeitspaket_2026-10-23_rounded_outlines.md).

`inputs/` enthält die zwölf vor Runtime-Änderung eingefrorenen Eingaben,
Prüfsummen, Beschreibungen und nativen Objektmarkierungen. `before/` erreicht
0/12; `final_cli/` erreicht mit neutralen Namen 12/12.
`additional/` und `final_additional_cli/` enthalten zwölf weitere synthetische
Fälle (Seed 918247), Ergebnis 12/12. `plan_b/` und `final_plan_b_cli/` enthalten
genau eine gekoppelte Vorlage samt 16 Größen-/Lagevarianten, Ergebnis 17/17.
Frühe positive Zwischenläufe bleiben lokal und sind keine finale Abnahme.

`final_existing_rounded_cli/` verwendet die zwölf Eingaben unter
`../rounded_composition_v1/development/`, Ergebnis 12/12.
`final_existing_split_cli/` verwendet die zwanzig Eingaben unter
`../component_splits_v1/input/`, Ergebnis 20/20.
`final_existing_residual_cli/` verwendet die neun Eingaben unter
`../residual_scene_v1/final-input/`, Ergebnis 7/9. Die zwei bekannten
kontrastarmen Fälle bleiben im Nenner.

Alle CLI-Versuche verwenden fünf Sekunden und Suchseed 17. Native Geometrie,
Radius, Konturbreite, Instanzen, Zeichenreihenfolge, Objektregionen und das
Originalraster werden unabhängig erneut geprüft. Die beiden Vektorzugriffswächter
müssen leer bleiben. Berichte, tatsächliche SVGs, Ergebniszeilen, Deadline- und
Workerprotokolle bleiben versioniert; abgeleitete Raster bleiben lokal.

`checks.json` und `logs/` enthalten die abschließenden gezielten Testresultate,
Syntax-/CLI-/ID-Prüfungen und den Runtime-Abgleich. Alle 422 gezielten Tests
(darunter 35 neue) bestehen; alle 39 bisherigen erfolgreichen CLI-Ausgaben
der Regressionskohorten sind bytegleich. Auch der in CI verwendete zusätzliche
Seed 942817 besteht mit 12/12 in einem frischen lokalen CLI-Lauf.
Die vollständige Standardsuite
wurde nicht erneut ausgeführt. `archive-hashes.json` belegt 758 unveränderte
Prüfsummen der 379 gespeicherten Paare; keine neue Archivkonvertierung oder
erneute Pixelprüfung wird daraus abgeleitet. Keine neue reale Familienabnahme.

```powershell
.venv/Scripts/python.exe -m tools.evaluate_rounded_composition --inputs artifacts/evaluation/rounded_outlines_v1/inputs --output artifacts/evaluation/rounded_outlines_v1/before --verify-only
.venv/Scripts/python.exe -m tools.evaluate_rounded_composition --inputs artifacts/evaluation/rounded_outlines_v1/inputs --output artifacts/evaluation/rounded_outlines_v1/final_cli --verify-only --require-all
.venv/Scripts/python.exe -m tools.evaluate_rounded_composition --inputs artifacts/evaluation/rounded_outlines_v1/additional --output artifacts/evaluation/rounded_outlines_v1/final_additional_cli --verify-only --require-all
.venv/Scripts/python.exe -m tools.evaluate_rounded_composition --inputs artifacts/evaluation/rounded_outlines_v1/plan_b --output artifacts/evaluation/rounded_outlines_v1/final_plan_b_cli --verify-only --require-all
```
