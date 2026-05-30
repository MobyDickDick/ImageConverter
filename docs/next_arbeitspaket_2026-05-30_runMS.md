# Nächstes Arbeitspaket – Run MS (2026-05-30)

Dieses Arbeitspaket arbeitet nach den abgeschlossenen Perception-First-Schritten
PF4/PF6 die nächste dokumentierte offene Aufgabe **PF5** ab: ein
Evaluationsharness, das Perception-Seeds nicht nur einzeln protokolliert, sondern
über Primitive hinweg messbar macht.

## 1) Nächste dokumentierte Aufgabe: PF5 Evaluationsharness

- Anlass:
  - `docs/open_tasks.md` markiert PF5 als nächste offene Perception-First-Aufgabe.
  - `docs/perception_first_task_backlog_2026-05-30.md` fordert Precision/Recall,
    Confidence-Verteilung, Renderfehler vor/nach Seed und den gewählten Call-Path
    für mindestens drei Primitive (`minus/line`, `circle/ring`, `rectangle`).
- Umsetzung:
  - `build_perception_seed_evaluation_record(...)` bewertet ein Sample von der
    Kandidatenerkennung über die Seed-Auswahl bis zum Renderfehlerdelta.
  - `summarize_perception_seed_evaluation(...)` aggregiert die Records zu
    Top-Candidate-Precision, Detection-Recall, Seed-Recall, Confidence-Statistik
    und mittlerem Qualitätsdelta pro Primitive-Familie.
  - Der CLI-Report `--report perception-seed-eval` schreibt JSON und CSV als
    PF5-Harness-Artefakte.

## 2) Gekoppelte Plan-B-/Repro-Aufgabe

- Synthetische Fixtures:
  - `minus_line_synthetic`
  - `circle_ring_synthetic`
  - `rectangle_synthetic`
- Realbild-Kopplung:
  - Wenn vorhanden, wird `artifacts/images_to_convert/AC0120_L.jpg` als realer
    Minus-/Plan-B-Kandidat mitgeführt.
  - Ein stabiler Realbild-Rechteckkandidat ist noch nicht dokumentiert und wird
    im Report unter `open_real_image_cases` explizit offengehalten.
- Artefakte:
  - `artifacts/evaluation/perception_seed_evaluation_v1/perception_seed_evaluation_report_v1.json`
  - `artifacts/evaluation/perception_seed_evaluation_v1/perception_seed_evaluation_samples_v1.csv`
- Ergebnis:
  - `samples=4`
  - `overall_detection_recall=1.0`
  - `overall_seed_recall=1.0`
  - `overall_top_candidate_precision=0.75`

## 3) Sichernde Tests und Checks

- Befehl:
  - `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/test_perception_seed_evaluation.py`
- Ergebnis:
  - Exit `0`
  - `2 passed, 5 warnings`
- Befehl:
  - `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/perception_detection_contract.py --report perception-seed-eval --output-dir artifacts/evaluation/perception_seed_evaluation_v1`
- Ergebnis:
  - Exit `0`
  - JSON-Summary mit `samples=4`, `overall_detection_recall=1.0` und
    `overall_seed_recall=1.0`.

## 4) Fazit

PF5 ist abgeschlossen: Der Perception-First-Track besitzt jetzt einen
reportbaren Evaluationsharness für mindestens drei Seed-Familien. Der nächste
sinnvolle Schritt ist **PF7**: einfache Glyph-/Text-Erkennung für `M`, `+`, `-`
und kurze Labels evaluieren, ohne neue Pflichtdependency einzuführen.
