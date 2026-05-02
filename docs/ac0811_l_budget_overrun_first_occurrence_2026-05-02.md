# AC08 Budgetüberschreitung – Erstauftreten und Folgeaufgabe (2026-05-02)

## Fragestellung
Bei welchem Bild trat im Vollbereichslauf `AC0800..AC0899` erstmals `validation_time_budget_exceeded` auf?

## Methode
Auswertung aller Batch-Logs `artifacts/converted_images/reports/AC0800_AC0899_batch_*.log` in chronologischer Reihenfolge und je Datei der **erste** Treffer auf `validation_time_budget_exceeded`.

## Ergebnis
- **Erstes Log mit `validation_time_budget_exceeded`:** `AC0800_AC0899_batch_2026-04-28_runAV.log`
- **Erstes betroffenes Bild darin:** `AC0811_L.jpg`
- **Trefferzeile:**
  - `[WARN] AC0811_L.jpg: ... validation_time_budget_exceeded: phase=round_start, round=2, elapsed=43.75s, budget=18.00s`

## Schlussfolgerung
`AC0811_L.jpg` ist der früheste belegte Trigger der Budgetüberschreitung im dokumentierten Vollbereichs-Logverlauf und bleibt auch in späteren Runs der erste Overrun-Kandidat.

## Abgeleitete Folgeaufgabe (höchste Priorität)
Gezielte Root-Cause-Analyse für `AC0811_L.jpg`:
1. Einzellauf nur `AC0811` mit detaillierter Anchor-/Runden-Telemetrie.
2. Zerlegen, welcher Teilpfad die Budgetzeit verbraucht (`round_start`, `element_loop`, `element=stem/arm`, ggf. Quality-Pass).
3. Konkrete Gegenmaßnahme implementieren (z. B. per-Element Early-Exit, AC0811-spezifische Budgetaufteilung, reduzierter Suchraum) und per Repro-Lauf validieren.
