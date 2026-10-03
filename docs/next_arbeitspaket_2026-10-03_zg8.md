# Nächstes Arbeitspaket – ZG8 dokumentierte Metrik-Hierarchie (2026-10-03)

Dieses Paket setzt nach ZG7 die nächste priorisierte P2-Aufgabe aus
`docs/umsetzungscheck_bild_semantik_2026-05-15.md` um: die verbindliche
Hierarchie der Qualitätsmetriken.

## Entscheidungsreihenfolge

Das Good-Solution-Gate veröffentlicht die Hierarchie im Gesamtbericht und in
jeder Einzelentscheidung:

1. **Primär:** `semantic_score` und `dimension_match` prüfen fachliche
   Korrektheit, Canvasgröße und Seitenverhältnis. Eine Verletzung dieser
   Schwellen kann durch keinen Pixelwert kompensiert werden.
2. **Sekundär:** `error_per_pixel` bewertet die visuelle Annäherung erst nach
   bestandenen Primärbedingungen.

Fehlende Pflichtmetriken oder terminale Quellstatus bleiben der vorgelagerten
Erreichbarkeitsentscheidung zugeordnet. Das Feld `decision_tier` nennt deshalb
pro Datei `reachability`, `primary`, `secondary` oder bei vollständig
bestandener Prüfung `all`. Bei verletzten Primärbedingungen enthält die
Gründenliste ausschließlich die fachlich vorrangigen Semantik- und
Dimensionsgründe; der Pixelwert wird dann nicht als konkurrierende Ursache
ausgegeben.

## Absicherung und nächster Schritt

Regressionstests belegen sowohl, dass ein perfekter Pixelwert eine verletzte
Semantikschwelle nicht aufwertet, als auch, dass der Pixelwert bei bestandenen
Primärmetriken weiterhin zu `suboptimal` führen kann. ZG8 ist damit
abgeschlossen. Die nächste priorisierte Leitaufgabe ist **ZG9 –
Taskboard-Verankerung** mit expliziten Akzeptanzkriterien und Exit-Bedingungen.
