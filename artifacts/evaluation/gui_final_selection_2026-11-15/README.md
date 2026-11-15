# GUI-Endauswahl und beschriebene Strichelung

[Diagnose und Änderungen](../../../docs/gui_best_preview_and_spray_dashes_2026-11-15.md).

- [Korrigierte SVG aus dem echten GUI-Backendlauf](corrected.svg)
- [Rastervorschau](corrected.png)
- [Abschliessendes Laufprotokoll](fresh_gui_final.log)
- [Abschliessender Jobstatus](fresh_gui_result.json)
- [Prüfung mit unabhängigem Renderer](independent_renderer.json)
- [Reproduktion der Ergebnisübernahme am kopierten ursprünglichen Job](replayed/replay.json)
- [Gezielte Python-Regressionen](tests_verified.log)
- [Zusätzliche GUI-/HTTP-Regressionen](gui_http_tests.log)
- [Kompakter Nachweis](summary.json)

`fresh_gui_jobs/` enthält die erhaltenen drei Entwicklungsläufe. Der erste
und zweite liefen weiterhin ins Budget; der dritte ist der erfolgreiche
Lauf mit korrigierter Journalisierung. `run_gui_repro.py` führt einen neuen
GUI-Backendlauf aus, ohne Katalog- oder Projektartefakte zu veröffentlichen.

Die konkreten frühen/späten SVGs, Raster und Beschreibung aus der Reklamation
sind als kleine Regression unter `tests/fixtures/gui_preview_selection/`
versioniert. Vollständige Protokolle und generierte Ausgaben bleiben gemäss
Projektkonvention lokal. Ursprüngliche GUI-Jobs werden nicht verändert.
