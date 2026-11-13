# Gelber Plan-B-Verlaufskreis

Ursache: Die Teilzeichenfolge `ring` in `geringfügig` verhinderte die
Radialkreisregistrierung bei neun Variantenbeschreibungen.

- Originalpaket: 14/17 Pixelpässe, drei Kantenfehler, keine Ausführungsfehler.
- Korrigierter CLI-Lauf: 17/17 Pässe mit identischen Eingaben und Budgets.
- Alle neuen Ausgaben: Hintergrundrechteck und nativer Verlaufskreis.
- Regressionen: 40 Radialkreistests und 22 Workbench-Tests bestanden.

`summary.json` enthält kompakte Messwerte, Hashes und Gegenproben.
`replay/` und `plan-b-workbench-corrected.zip` bleiben lokale Artefakte.
Die Untersuchung und Grenzen sind in
[der Diagnose](../../../docs/plan_b_yellow_disk_2026-11-13.md) dokumentiert.
