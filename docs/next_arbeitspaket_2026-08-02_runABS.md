# Nächstes Arbeitspaket – Optimierungs-Telemetrie Batch-Summary Run ABS (2026-08-02)

Run ABS setzt den in Run ABR dokumentierten nächsten Schritt um: Die pro
Konversion persistierten Render-Timeouts und Renderfehler werden in der
Post-Conversion-Finalisierung zu einer maschinenlesbaren Batch-Summary
zusammengeführt.

## 1) Batch-Vertrag

Jeder abgeschlossene Konvertierungslauf schreibt
`optimization_render_telemetry_summary.json`. Das versionierte Dokument enthält
die Anzahl der Ergebniszeilen, die Summen `render_timeouts` und `render_errors`
sowie die Anzahl betroffener Varianten. `affected_variants` führt nur
Ergebniszeilen mit mindestens einem Ereignis auf und enthält Dateiname,
normalisierte Variante und beide Zähler.

Die Liste wird nach Variante und Dateiname sortiert. Dadurch bleibt das Artefakt
bei identischen Ergebnissen deterministisch und kann zwischen Batch-Läufen
direkt verglichen werden. Ein leerer oder ereignisfreier Batch erzeugt ebenfalls
eine gültige Summary mit Nullsummen und leerer Variantenliste.

## 2) Kompatibilität

Die Aggregation verwendet denselben öffentlichen Telemetrievertrag wie das
`Iteration_Log.csv`: Der öffentliche Snapshot hat Vorrang; ältere interne
`timeouts`-/`errors`-Zähler werden weiterhin übernommen. Damit divergieren
Detail-CSV und Batch-Summary nicht bei wiederaufgenommenen älteren Checkpoints.

## 3) Regressionstests und nächster Schritt

Helper-Tests sichern Summen, Variantenfilterung, deterministische Reihenfolge,
Vorrang des öffentlichen Snapshots und den leeren Batch ab. Der
Finalisierungstest stellt zusätzlich sicher, dass die Summary im normalen
Post-Conversion-Pfad geschrieben wird.

Als nächstes kann ein Vergleichsreport die Summary des aktuellen Laufs gegen
eine explizit gewählte Baseline stellen und Zählerdifferenzen ausweisen, ohne
laufübergreifenden Zustand in den Konversionsalgorithmus einzubauen.
