# Kreuzpanel mit Plus/Minus: korrigierte Plan-B-Serie

[Diagnose, Korrekturen und Grenzen](../../../docs/crossed_panel_workbench_2026-11-16.md).

- [Alle 17 Fälle: Original, korrigierte Ausgabe und Differenz](all_cases_comparison.png)
- [Korrigiertes Workbench-ZIP](corrected-plan-b-workbench.zip)
- [Frischer CLI-Lauf](replay.log)
- [Alle Ergebnisse des Laufs](replay_results.json)
- [Zwei Renderer und neue Strukturprüfung](renderer_checks.json)
- [Nachprüfung der alten grünen Ausgaben](old_recheck.json)
- [Veröffentlichte separate Kopie in der GUI-Workbench](published_run.json)
- [Gezielte Regressionen](tests_final.log)
- [Ältere Modellsuite](model_regressions.log)
- [Isolierte Kleinstbild-Wiederholung](small_regression_isolation.log)
- [Kleinstbild-Vergleich mit dem unveränderten HEAD-Modell](small_baseline_check.log)
- [Kompakter versionierter Nachweis](summary.json)

`imported/` enthält eine unveränderte, pfadgeprüft extrahierte Kopie des
Nutzer-ZIPs. `fresh_cli/` enthält den frischen Lauf ohne Referenzzugriff durch
den Konverter. `replay.py` kann weitere Versuche mit denselben 17 Eingaben
und demselben Seed ausführen. Die generierten Artefakte bleiben gemäss
Projektkonvention lokal; kleine dauerhafte Regressionen liegen unter
`tests/fixtures/crossed_panel_seed34/`.
