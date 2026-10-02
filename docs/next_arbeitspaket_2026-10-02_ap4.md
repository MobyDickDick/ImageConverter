# Nächstes Arbeitspaket – AP4 Report-Konsistenzgate (2026-10-02)

Dieses Paket setzt **AP4** aus
`next_arbeitspakete_aus_artifacts_2026-10-01.md` um. Das neue lokale Gate
`tools/check_report_consistency.py` prüft Checkpoint, Result-Map,
Abschlussmanifest, Fehlerliste und Chain-Telemetrie gemeinsam, bevor Reports
als belastbarer Kataloglauf ausgewertet werden.

## Status- und Provenienzvertrag

Der maschinenlesbare Gate-Report besitzt die Pflichtfelder `schema_version`,
`run_id`, `generated_at`, `input_count`, `processed_count` und `source_report`.
Er unterscheidet vier Zustände:

- `complete`: Checkpoint, Manifest und Zähler beschreiben denselben
  abgeschlossenen Lauf.
- `incomplete`: Der konsistente Checkpoint ist noch nicht finalisiert; dieser
  Zustand ist ausdrücklich kein fachlicher Pass.
- `stale/mixed-run`: Zähler, Run-IDs oder nichtleere Result-Map und leere
  Summary widersprechen einander. Die CLI endet ungleich null.
- `invalid`: Ein Report ist syntaktisch oder strukturell ungültig, ein
  Dateiname doppelt oder ein referenziertes Log fehlt. Die CLI endet ebenfalls
  ungleich null.

## Aktueller Snapshot und Integration

Der eingecheckte partielle Snapshot wird erwartungsgemäß als
`stale/mixed-run` erkannt: `conversion_result_map.json` ist nicht leer, während
`chain_phase_telemetry_summary.txt` `conversion_count=0` meldet. Damit kann
dieser Altstand nicht mehr versehentlich als erfolgreicher Abschluss gelten.

Das Gate ist in `tools/run_local_completion_checks.sh` vor dem bestehenden
Chain-Drift-Gate eingebunden. Fixture-Tests decken einen konsistenten
abgeschlossenen Lauf, einen konsistenten partiellen Lauf, den aktuellen
Null-Summary-Widerspruch sowie doppelte Dateinamen und fehlende Logreferenzen
ab. Als nächster Schritt kann AP3 nach einem tatsächlich abgeschlossenen AP0-
Lauf seine Qualitätswarteschlange ausschließlich aus einem `complete`-Stand
neu bilden.
