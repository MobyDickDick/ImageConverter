# Nächstes Arbeitspaket – Run MU (2026-05-30)

Dieses Arbeitspaket schließt nach PF7 die nächste dokumentierte offene
Perception-First-Aufgabe **PF8** ab: Die aktive Plan-B-Rotation wird mit einem
verbindlichen Abschnitt „Perception-Lerneffekt“ verzahnt.

## 1) Nächste dokumentierte Aufgabe: PF8 Plan-B-/Perception-Verzahnung

- Anlass:
  - `docs/open_tasks.md` markierte PF8 als nächste offene
    Perception-First-Aufgabe.
  - `docs/perception_first_task_backlog_2026-05-30.md` fordert, dass kommende
    Plan-B-Pakete jeweils genau eine Perception-Frage dokumentieren.
- Umsetzung:
  - `PLAN_B_PERCEPTION_TARGETS` beschreibt die aktiven Kandidaten
    `AC0224_S`, `AC0231_S`, `AC0838_M` und `AC0881_M` mit Plan-B-Grund,
    Perception-Frage, erwartetem ersten Primitive und Seed-Erwartung.
  - `build_plan_b_perception_linkage_record(...)` wertet die vorhandenen
    Detectoren auf dem realen Kandidatenbild aus und schreibt je Kandidat einen
    Abschnitt `perception_lerneffekt`.
  - Der neue CLI-Report `--report plan-b-perception-linkage` erzeugt JSON und
    CSV mit Entscheidungen aus `generalisiert`, `nur Sonderfall` oder
    `noch nicht erkannt`.

## 2) Gekoppelte Plan-B-/Repro-Aufgabe

- Artefakte:
  - `artifacts/evaluation/plan_b_perception_linkage_v1/plan_b_perception_linkage_report_v1.json`
  - `artifacts/evaluation/plan_b_perception_linkage_v1/plan_b_perception_linkage_samples_v1.csv`
- Ergebnis:
  - `samples=4`
  - `evaluated_samples=4`
  - `all_have_perception_lerneffekt=true`
  - Entscheidungen:
    - `AC0224_S`: `generalisiert` über Kreis-/Ring-Signal → `CircleBackground`
    - `AC0231_S`: `generalisiert` über Kreis-Signal → `CircleBackground`, `M`
      bleibt als Label-Hinweis dokumentiert
    - `AC0838_M`: `generalisiert` über Kreis-Signal → `CircleBackground`, `VOC`
      bleibt als Label-Hinweis dokumentiert
    - `AC0881_M`: `generalisiert` über Kreis-/HorizontalRule-Signale →
      `CircleBackground`/`HorizontalRule`
- Prozessänderung:
  - `PLAN_B_KANDIDATEN.md` enthält ab sofort den Pflichtabschnitt
    „Perception-Lerneffekt“ mit Frage, erwartetem Primitive, Entscheidung und
    Seed-Folge pro aktivem Kandidaten.

## 3) Sichernde Tests und Checks

- Befehl:
  - `python -m pytest -q tests/test_plan_b_perception_linkage.py`
- Ergebnis:
  - Exit `0`
  - `2 passed`
- Befehl:
  - `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/perception_detection_contract.py --report plan-b-perception-linkage --output-dir artifacts/evaluation/plan_b_perception_linkage_v1`
- Ergebnis:
  - Exit `0`
  - JSON-Summary mit `samples=4`, `evaluated_samples=4` und
    `all_have_perception_lerneffekt=true`.

## 4) Fazit

PF8 ist abgeschlossen: Die Plan-B-Liste ist nicht mehr nur eine lineare
Nachzeichnungsliste, sondern trägt pro Kandidat einen expliziten
Perception-Lerneffekt. Der nächste sinnvolle Schritt ist die normale
Plan-B-Rotation mit Übernahme dieses Pflichtabschnitts in das jeweils konkrete
Kandidatenpaket.
