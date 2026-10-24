# Wiederholte Füllfarben in gemischten Überdeckungsszenen

`summary.json` erhält den kontrollierten CLI-Vergleich **0/12 → 12/12**, den
zusätzlichen Seed **12/12** und genau eine gekoppelte Plan-B-Vorlage mit
**17/17** Fällen. Eingabehashes sind im Vergleich identisch; Ausgangsmodul und
endgültiges Modul sind über ihre SHA-256-Werte gebunden. Je Fall bleiben
Ausgabehash, unabhängige Objekt-/Regions-/Pixelmessungen, Rückgabecode und
Laufsteuerung erhalten. Es gelten fünf Sekunden je Bild und Suchseed 17.

`checks.json` dokumentiert die Testsignale. Generierte Eingaben, SVGs und
CLI-Bäume gehören zu den temporären Arbeitsdaten. Wiederholung ohne dauerhafte
Raster-/Vektorablage:

```powershell
python -m tools.run_seeded_scene_check evaluate_mixed_overlap --seed 527183 --children 6 --repeat-fill --rounded --outlines
python -m tools.run_seeded_scene_check evaluate_mixed_overlap --seed 918527 --children 6 --repeat-fill --rounded --outlines
python -m tools.run_seeded_scene_check evaluate_mixed_overlap --seed 342781 --children 6 --repeat-fill --rounded --outlines --variations
```

Die Baseline verwendet denselben Generator und das unveränderte produktive
Modul aus `93822e748`. Ein mit Entwicklungsänderungen überlappender früherer
Versuch ist nicht Teil dieses Vergleichs. Die positive Abnahme gilt für
synthetische Entwicklung, nicht für unabhängige reale Familien.
Details: [Arbeitspaket](../../../docs/next_arbeitspaket_2026-10-24_repeated_fill.md).
