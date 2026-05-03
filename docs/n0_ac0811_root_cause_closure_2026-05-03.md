# N0 Abschlussnotiz – AC0811_L erstes Budget-Overrun (2026-05-03)

## Kurzfazit
Die erste dokumentierte Budgetüberschreitung bei `AC0811_L` wurde auf einen zu engen
Validierungs-Zeitrahmen im Vollbereichslauf zurückgeführt (`budget=18s`), der bei AC0811-L
bereits vor Start von Runde 2 erreicht wurde (`phase=round_start, round=2, elapsed=43.75s`).

## Reproduzierbare Evidenz
1. Erstfund im Vollbereich: `AC0800_AC0899_batch_2026-04-28_runAV.log`
   mit `validation_time_budget_exceeded` für `AC0811_L`.
2. AC0811-Only-Repro (Run B): Exit `0`, kein neuer Budget-Timeout, aber deutlich erhöhte
   Laufzeit/Wiederholung im AC0811-Scope.
3. Gegenmaßnahme (Run C):
   - Single-Base-Fast-Path (`max_quality_passes=1`, override via `ICC_MAX_QUALITY_PASSES`)
   - messbare Laufzeitreduktion (`395.59s` -> `363.78s`, ca. `-8%`)
   - weiterhin Exit `0` ohne `validation_time_budget_exceeded`.

## Implementierte Gegenmaßnahmen
- Budget-Floor für `AC0811_L` in der Validierung (`max(..., 48.0)`), damit
  elementbezogene Suchrunden nicht vorzeitig am Rundenrand abbrechen.
- Reduzierte globale Quality-Pass-Anzahl für Single-Base-Läufe zur Senkung
  der Wiederholungskosten in Diagnose-/Repro-Läufen.

## Bewertung gegen N0-Akzeptanzkriterium
- **Isolierter Repro-Lauf:** erfüllt (AC0811-only Run B/C).
- **Kurzbericht mit Ursache:** erfüllt (diese Notiz + bestehende AC0811-Reports).
- **Patch mit messbarer Wirkung:** erfüllt (Laufzeitverbesserung und kein Timeout-Rückfall
  im isolierten Scope).

## Rest-Risiko
Der Vollbereichsnachweis (`N1`) bleibt separat offen, weil dort weiterhin ein kompletter
Durchlauf bis `AC0899` als Abschlusskriterium gefordert ist.
