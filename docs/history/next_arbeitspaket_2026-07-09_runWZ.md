# Nächstes Arbeitspaket – Batch-Checkpoint Resume-Reader Run WZ (2026-07-09)

Run WZ setzt den nach Run WY dokumentierten Anschluss um: Der während langer
Batch-Läufe geschriebene `conversion_checkpoint.json` verweist bereits auf den
aktuellen `conversion_result_map.json`-Snapshot; nun gibt es zusätzlich einen
kleinen, robusten Reader, der diesen Snapshot für Resume- und Audit-Werkzeuge
wieder als `result_map` laden kann.

## 1) Umsetzung

- `loadConversionCheckpointResultMapImpl(...)` liest ein inkrementelles
  Checkpoint-Artefakt und löst `result_map_path` relativ zum Reports-Verzeichnis
  oder als absoluten Pfad auf.
- Ungültige, fehlende oder ältere Checkpoint-/Snapshot-Artefakte liefern bewusst
  eine leere Map zurück. Damit können spätere Resume-Aufrufer ohne eigenen
  Fehlerpfad auf einen kalten Lauf zurückfallen.
- Der Reader normalisiert nur echte Mapping-Zeilen in die zurückgegebene
  `dict[str, dict[str, object]]`-Struktur und ignoriert fehlerhafte Einträge.

## 2) Perception-Lerneffekt

Run WZ erweitert keine Perception-Erkennung. Der Lerneffekt bleibt operativ:
Plan-B- und lange Batch-Läufe sind nicht nur früher persistiert, sondern können
über den Checkpoint auch maschinell wieder in einen `result_map`-Zwischenstand
zurückgeführt werden.

## 3) Sicherung

- `python -m pytest -q tests/detailtests/test_batch_reporting_helpers.py::test_load_conversion_checkpoint_result_map_reads_relative_snapshot tests/detailtests/test_batch_reporting_helpers.py::test_load_conversion_checkpoint_result_map_ignores_invalid_artifacts` läuft grün mit `2 passed`.

## 4) Ergebnis / nächster Schritt

Run WZ schließt den Resume-Reader-Folgepunkt ab. Checkpoint-Reader und
Result-Map-Snapshot bilden jetzt eine nachvollziehbare Persistenzkette; weitere
Arbeitspakete können wieder in der aktiven Plan-B-Rotation fortfahren oder einen
vollständigen Resume-Modus auf Basis dieses Readers ergänzen.

Aktueller Aufgabenstand: `docs/open_tasks.md` enthält `37` offene
Checkbox-Aufgaben bei `404` erkennbaren Checkbox-Aufgaben insgesamt.
