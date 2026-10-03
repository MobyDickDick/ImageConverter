# Nächstes Arbeitspaket – ZG7.4 Mehrzieloptimierung (2026-10-03)

Dieses Paket setzt nach ZG7.3 den vierten Schritt der dokumentierten Folge
`ZG7.1 → ZG7.2 → ZG7.3 → ZG7.4 → ZG7.5 → ZG7.6` um. Die Optimierung arbeitet
ausschließlich innerhalb der vom Constraint-Fusion-Beam zugelassenen
Topologien.

## Zweiphasiger Optimierungsvertrag

`tools/optimize_geometry_ir.py` erzeugt den versionierten Record
`multi_objective_optimization_report_v1`. In der diskreten Phase wird unter
den semantisch zulässigen Hypothesen die beste Primitive-Zuordnung und
Z-Reihenfolge gewählt. Danach verändert eine deterministische grob-zu-feine
Suche Position, Größe, Kontur, Farbe und Gradientenparameter innerhalb einer
Trust-Region. Die Zielfunktion protokolliert Pixel-, Edge-, Struktur- und
Semantikverlust sowohl einzeln als auch gewichtet als Gesamtverlust.

Eine Iteration wird nur angenommen, wenn ihr Gesamtverlust strikt sinkt und
alle harten Constraints weiter gelten. Damit sind Oszillation und eine
semantische Regression ausgeschlossen. Budget und Stagnationsgrenze sind
explizit; die kanonischen Abschlussgründe lauten `budget_exceeded`,
`stagnation`, `converged` und bei einem unzulässigen Eingangs-Beam
`semantic_conflict`. Die CLI kann neben dem JSON-Report eine Konvergenz-CSV
schreiben.

## Abnahme

Der maschinenlesbare Beleg unter
`artifacts/evaluation/multi_objective_optimization_report_v1/report_2026-10-03.json`
enthält die drei ZG7-Fixtures. In allen drei Fällen bleibt die Topologie hart
geschützt; bei `circle_text_connector` und `rectangle_diagonal` sinkt der
Gesamtverlust gegenüber der Initialhypothese. Damit ist die geforderte
Verbesserung für mindestens zwei von drei Fixtures nachgewiesen.

ZG7.4 ist abgeschlossen. Das nächste dokumentierte Paket ist **ZG7.5 –
Baseline und hartes Zufriedenheitsgate**.
