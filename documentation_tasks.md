# Aufgabenliste: Dokumentation des Image-Konverters

Diese Aufgabenliste wurde auf Themen bereinigt, die in diesem Repository-Snapshot
wirklich den Image-Konverter betreffen. Historische Tiny-Language-/Compiler-
/Runtime-Aufgaben wurden entfernt, damit die Liste als Arbeitsgrundlage für den
aktuellen Projektfokus nutzbar bleibt.

## Abgeschlossene Dokumentations- und Strukturaufgaben

- [x] Jede Sourcecodedatei des Image-Konverters ist so detailliert wie sinnvoll dokumentiert (inklusive Kontext/Begründungen für größere Zusammenhänge).
- [x] Große Sourcecodedateien sind in überschaubare, logisch getrennte kleinere Dateien aufgeteilt (inkl. ggf. neuer Modulstruktur und aktualisierten Importpfaden).
- [x] AC08-Aufgabe 1.1 ist erledigt: Qualitäts-/Tercile-Pässe übernehmen nur noch echte Verbesserungen und protokollieren Regressionen explizit. (siehe `docs/ac08_improvement_plan.md`)
- [x] AC08-Aufgabe 5.1 ist erledigt: Ein festes Regression-Set inkl. reproduzierbarem CLI-Workflow und Manifest/Report-Dateien ist definiert. (siehe `docs/ac08_improvement_plan.md`)
- [x] AC08-Aufgabe 5.2 ist erledigt: Schriftlich fixierte Erfolgskriterien inkl. maschinenlesbarem Report für das Regression-Set sind definiert. (siehe `docs/ac08_improvement_plan.md`)

## Verweis auf offene, noch relevante Arbeiten

- Die verbleibenden offenen Punkte für den Image-Konverter werden in `docs/open_tasks.md` gepflegt; aktuell enthält die kanonische Liste keine offenen Einträge.
- Die im AC08-Plan beschriebene laufende Nachverfolgung offener Schwachfamilien ist für diesen Snapshot als Artefaktstand unter `artifacts/converted_images/reports/ac08_weak_family_status.csv` und `.txt` materialisiert.
- AC08-spezifische Verbesserungen und deren Priorisierung stehen in `docs/ac08_improvement_plan.md`.
