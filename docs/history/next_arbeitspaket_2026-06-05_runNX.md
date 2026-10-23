# Nächstes Arbeitspaket – Run NX (2026-06-05)

Dieses Arbeitspaket setzt den in FP-D12 dokumentierten Recovery-Plan vor FP-D13
um: Der feste AC08-Regressionssatz wird nicht mehr als ein einziger, global
limitierter Konverterprozess ausgeführt.

## Fehlerbild

Der harte Gate-Lauf erreichte auch mit 900 Sekunden nur sechs von vierzehn
Varianten. Dadurch fehlte die vollständige Reportkette und eine alte oder
partielle `ac08_success_metrics.csv` durfte nicht als Release-Nachweis gelten.

## Umsetzung

- Der neue CLI-Schalter `--ac08-regression-variant` begrenzt den festen Satz exakt auf ein Segment.
- `tools/run_ac08_segmented_smoke.sh` startet jede feste AC08-Variante in einem
  eigenen Ausgabeverzeichnis mit separatem Timeout, Log und Statusdatensatz.
- Erfolgreiche Segmente erhalten einen `.segment-complete`-Marker. Sobald ein
  Segment fehlschlägt, wird der Lauf als Blocker beendet und die Aggregation
  ausdrücklich zurückgehalten.
- `tools/finalize_ac08_segmented_run.py` akzeptiert nur den vollständigen festen
  14-Varianten-Satz, kopiert dessen Bild-/SVG-/Validierungsartefakte, führt
  `Iteration_Log.csv` und `quality_tercile_passes.csv` zusammen und erzeugt erst
  danach Manifest und AC08-Gesamtmetrik.
- Der Release-Candidate-Runner verwendet diesen segmentierten Smoke nun als
  Standard; `RC_GATE_AC08_SMOKE_CMD` bleibt für kontrollierte Tests/Diagnosen
  überschreibbar.

## Nachweis

Die Detailtests prüfen:

1. Ein fehlgeschlagenes Segment erzeugt einen `BLOCKER` und keine Aggregation.
2. Vollständig grüne Segmente starten genau einmal die Finalisierung.
3. Fehlende Marker verhindern die Gesamtmetrik.
4. Eine synthetisch vollständige 14-Varianten-Artefaktkette wird zu
   `images_converted=14`, `images_missing=0` und `overall_success=1`
   aggregiert.

## Nächster Schritt

FP-D13 kann nun den realen finalen End-to-End-Lauf segmentiert ausführen und die
aggregierte Metrik quantitativ gegen die Baseline vergleichen.
