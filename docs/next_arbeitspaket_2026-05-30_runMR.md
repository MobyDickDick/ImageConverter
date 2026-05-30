# Nächstes Arbeitspaket – Run MR (2026-05-30)

Dieses Arbeitspaket arbeitet nach Run MP die nächste dokumentierte
Perception-First-Aufgabe **PF6** ab: Perception-Telemetrie früh als JSON/CSV
sichtbar machen. Damit ist nachvollziehbar, welche Kandidaten erkannt, welche
abgelehnt und welche als Geometry-IR-Seed gewählt wurden.

## 1) Nächste dokumentierte Aufgabe: PF6 Perception-Telemetrie

- Anlass:
  - `docs/next_arbeitspaket_2026-05-30_runMP.md` nennt PF6 als nächsten
    sinnvollen Schritt, bevor weitere Kandidaten unsichtbar in Runtime-Pfaden
    verschwinden.
  - `docs/perception_first_task_backlog_2026-05-30.md` fordert pro Lauf eine
    CSV/JSON-Spur mit erkannten und abgelehnten Kandidaten, gewähltem Seed sowie
    Fehlerwerten vor/nach Seed.
- Umsetzung:
  - `build_perception_telemetry_record(...)` erstellt einen stabilen
    Telemetrie-Record mit Candidate-Entscheidungen, Seed-Liste,
    Geometry-IR-Kinds vor/nach Seed und Fehlerdelta.
  - `write_perception_telemetry_report(...)` schreibt denselben Record als
    JSON-Report und flache CSV-Kandidatenliste.
  - Der CLI-Report `--report perception-telemetry` erzeugt ein einzelnes
    Plan-B-taugliches Report-Artefakt.

## 2) Gekoppelte Plan-B-/Repro-Aufgabe

- Einzelkandidat:
  - Bild: `artifacts/images_to_convert/AC0120_L.jpg`.
  - Beschreibungshinweis: oben auf der vertikalen Symmetrieachse werden ein
    `+`- und ein `-`-Zeichen eingefügt.
- Artefakte:
  - `artifacts/evaluation/perception_telemetry_v1/perception_telemetry_report_v1.json`
  - `artifacts/evaluation/perception_telemetry_v1/perception_telemetry_candidates_v1.csv`
- Ergebnis:
  - `samples=1`
  - `all_have_selected_seed=true`
  - Kandidatenentscheidungen und Fehlerwerte vor/nach Seed werden protokolliert.

## 3) Sichernde Tests und Checks

- Befehl:
  - `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/test_perception_telemetry_report.py`
- Ergebnis:
  - Exit `0`
  - `2 passed, 5 warnings`
- Befehl:
  - `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/perception_detection_contract.py --report perception-telemetry --output-dir artifacts/evaluation/perception_telemetry_v1`
- Ergebnis:
  - Exit `0`
  - JSON-Summary mit `samples=1`, `accepted_candidates=3` und `all_have_selected_seed=true`.

## 4) Fazit

PF6 ist abgeschlossen: Der Perception-First-Track besitzt jetzt ein reportbares
Telemetrieformat für Kandidaten, Ablehnungsgründe, ausgewählte Geometry-IR-Seeds
und Fehlerdeltas. Der nächste sinnvolle Schritt ist **PF5**: ein
Evaluationsharness, das diese Telemetrie für mindestens drei Primitive zu
Precision/Recall, Confidence-Verteilung und Qualitätsänderung verdichtet.
