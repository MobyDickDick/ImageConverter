# Nächstes Arbeitspaket – strukturierter Optimierungsreport Run ABR (2026-08-02)

Run ABR setzt den in Run ABQ dokumentierten nächsten Schritt um: Die getrennten
Zähler für Render-Timeouts und reguläre Renderfehler werden nicht mehr nur in
Textlogs ausgegeben, sondern als strukturierte Konversionsdaten persistiert.

## 1) Stabiler Ergebnisvertrag

Jede erfolgreiche Konversionszeile enthält
`optimization_render_telemetry` mit den nichtnegativen Ganzzahlfeldern
`render_timeouts` und `render_errors`. Der öffentliche Snapshot wird aus der
laufenden Optimierungstelemetrie erzeugt und gelangt dadurch auch in
`conversion_result_map.json` sowie in inkrementelle Checkpoints.

## 2) Aggregierbares Iterationsartefakt

`Iteration_Log.csv` erhält die Spalten `Render-Timeouts` und `Render-Fehler`.
Ältere oder nicht optimierte Ergebniszeilen werden kompatibel als `0;0`
ausgegeben. Beim Einlesen interner älterer Zeilen akzeptiert der Export weiterhin
die bisherigen Schlüssel `timeouts` und `errors`; ein vorhandener öffentlicher
Snapshot hat Vorrang.

## 3) Regressionstests und nächster Schritt

Helper-Tests sichern den CSV-Vertrag, Nullwerte ohne Telemetrie, die Übernahme
der bisherigen internen Zähler und den Vorrang des öffentlichen Snapshots ab.

Als nächstes kann die Post-Conversion-Berichterstattung eine Batch-Summary mit
Summen und betroffenen Varianten ergänzen. So ließen sich Budgetengpässe direkt
zwischen vollständigen Konvertierungsläufen vergleichen.
