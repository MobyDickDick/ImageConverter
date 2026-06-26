# Nächstes Arbeitspaket – Plan-B Qualitätsrefresh Run TD (2026-06-26)

Run TD arbeitet nach Run TC den nächsten dokumentierten Pflege-Schritt aus
`PLAN_B_KANDIDATEN.md` ab: Nach Abschluss der fünf aktiven Plan-B-Kandidaten
wird der reproduzierbare Qualitätsreview erneut ausgeführt und die Rotation gegen
die aktuelle Diff-Triage geprüft.

## Änderungen

- Der Review `tools/review_conversion_quality.py --max-candidates 5` wurde erneut
  gegen die aktuelle Conversion-/Diff-Artefaktlage ausgeführt.
- Die Plan-B-Rotation bleibt stabil: `DLG0021`, `GE1410_L`, `SE0041_1`,
  `GE9012_6M` und `GE9013_1M` sind weiterhin die fünf qualifizierten kompakten
  Diff-Fälle oberhalb der Review-Grenze.
- `PLAN_B_KANDIDATEN.md` dokumentiert den Refresh-Stand jetzt explizit als Run TD
  und hält fest, dass kein neuer Kandidat nachrücken musste.

## Perception-Lerneffekt

- Kein neuer Perception-Contract wurde ergänzt. Die gekoppelten Lerneffekte aus
  Run SS bis Run TC bleiben gültig: `GE1410_L` ist `generalisiert`, während
  `DLG0021`, `SE0041_1`, `GE9012_6M` und `GE9013_1M` weiterhin auf
  beschreibungsbasierte Sonderfall-Contracts beziehungsweise manuelle Seed-
  Annahmen angewiesen sind.

## Artefakte

- `artifacts/evaluation/conversion_quality_review_v2/conversion_quality_review_v2.json`
- `artifacts/evaluation/conversion_quality_review_v2/plan_b_candidate_triage_v1.csv`
- `artifacts/evaluation/conversion_quality_review_v2/conversion_quality_records_v2.csv`

## Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/review_conversion_quality.py --max-candidates 5` läuft grün und meldet `selected_candidates=5` mit unveränderter Reihenfolge `DLG0021,GE1410_L,SE0041_1,GE9012_6M,GE9013_1M`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün und meldet weiterhin `0 occurrences`.

## Ergebnis

Der dokumentierte Plan-B-Pflegeschritt ist abgeschlossen. Die Review-Artefakte
sind reproduzierbar aktualisiert beziehungsweise bestätigt, und die aktive
Kandidatenliste bleibt nach dem Run-TD-Refresh unverändert. Der nächste sinnvolle
Schritt ist wieder ein gezieltes kleines Feintuning innerhalb dieser stabilen
Rotation, bevorzugt bei einem der weiterhin klar oberhalb der Review-Grenze
liegenden Kandidaten.
