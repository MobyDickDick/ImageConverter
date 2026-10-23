# Nächstes Arbeitspaket – ZG6 robuste Nicht-Erreichbarkeit (2026-10-03)

Dieses Paket setzt nach ZG5 die nächste priorisierte P1-Aufgabe aus
`docs/umsetzungscheck_bild_semantik_2026-05-15.md` um: eine einheitliche,
reproduzierbare Klassifikation nicht erreichbarer Konvertierungsergebnisse.

## Einheitlicher Vertrag

Alle heterogenen Status-, Grund- und Detailangaben werden deterministisch auf
vier öffentliche Gründe abgebildet:

| Grund | Report-Code | Exit-Code |
| --- | --- | ---: |
| `stagnation` | `NR001` | 20 |
| `budget_exceeded` | `NR002` | 21 |
| `dimension_violation` | `NR003` | 22 |
| `semantic_conflict` | `NR004` | 23 |

Treffen mehrere Signale zu, gilt die feste Priorität
`dimension_violation`, `semantic_conflict`, `budget_exceeded`, `stagnation`.
Unbekannte Fehler fallen konservativ auf `stagnation` zurück; sie erfinden
damit keinen nicht belegten Constraint- oder Budgetverstoß.

## Reports und Prozessstatus

`batch_failure_summary.csv` enthält neben den unveränderten Rohangaben nun die
Spalten `reachability_reason`, `report_code` und `exit_code`. Das
Good-Solution-Gate gibt dieselben Angaben pro `not_reachable`-Bewertung im
Objekt `reachability` aus. Sein Schalter `--fail-on-not-reachable` aktiviert
die kanonischen Exit-Codes für automatisierte Gates; ohne den Schalter bleibt
das bisherige reine Reporting mit Exit-Code 0 kompatibel.

## Absicherung und nächster Schritt

Unit- und CLI-Tests prüfen alle vier Zuordnungen, die feste Priorität, den
Fallback, die CSV-Spalten sowie einen realen Exit-Code. ZG6 ist damit
abgeschlossen. Die nächste priorisierte Leitaufgabe ist das P1-Benchmark-Set
ohne Sonderwissen.
