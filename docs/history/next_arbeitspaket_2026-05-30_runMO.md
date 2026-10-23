# Nächstes Arbeitspaket – Run MO (2026-05-30)

Dieses Arbeitspaket rotiert nach Run MN in den neu priorisierten
Perception-First-Track. Die nächste dokumentierte Aufgabe ist **PF1**: ein
stabiler Detection-Contract für erkannte Primitive, bevor PF2/PF3 konkrete
Erkennungen als Geometry-IR-Seeds nutzen.

## 1) Nächste dokumentierte Aufgabe: PF1 Detection-Contract v1

- Anlass:
  - `docs/open_tasks.md` priorisiert ab 2026-05-30 den Perception-First-Track
    vor weiterer Einzelfall-Rotation.
  - `docs/perception_first_task_backlog_2026-05-30.md` fordert für PF1 ein
    maschinenlesbares Zwischenformat mit `kind`, `bbox`, `center`,
    geometrischen Parametern, Farbe, `confidence`, `roi`, `evidence` und
    `source`.
- Umsetzung:
  - Neues Modul `tools/perception_detection_contract.py` definiert den
    serialisierbaren Dataclass-Contract `PerceptionPrimitiveCandidate` mit
    `schema_version="perception_primitive_candidate_v1"`.
  - Bestehende Linien- und Konturhilfen werden in denselben Contract überführt:
    `line` aus Canny/Hough, `circle` aus Kontur-Circularity und `rectangle` aus
    konvexen Vierpunkt-Konturen.
  - Der Contract enthält direkt die für spätere Geometry-IR-Seeds relevanten
    Felder: Bounding-Box, Mittelpunkt, primitive-spezifische Geometrie,
    robuste Farbprobe, ROI, Evidence und Source.

## 2) Gekoppelte Plan-B-Aufgabe: synthetischer Contract-Report

- Anlass:
  - Das PF1-Backlog erlaubt als Plan-B, zunächst mit drei synthetischen Szenen
    (`minus`/Linie, `circle`, `rectangle`) zu arbeiten, falls Realbilder noch zu
    unsicher sind.
- Umsetzung:
  - `run_contract_report()` erzeugt drei synthetische Fixtures (`line`,
    `circle`, `rectangle`) und schreibt einen JSON-Report.
  - Artefakt:
    `artifacts/evaluation/perception_detection_contract_v1/perception_detection_contract_v1_report.json`.
- Ergebnis:
  - `samples=3`
  - `all_matched=true`
  - Die akzeptierten Contract-Kinds sind `line`, `circle` und `rectangle`.

## 3) Sichernde Tests und Checks

- Befehl:
  - `python -m pytest tests/test_perception_detection_contract.py -q`
- Ergebnis:
  - Exit `0`
  - `2 passed`
- Befehl:
  - `python tools/perception_detection_contract.py --output-dir artifacts/evaluation/perception_detection_contract_v1`
- Ergebnis:
  - Exit `0`
  - JSON-Summary mit `samples=3` und `all_matched=true`.
- Befehl:
  - `python -m pytest tests/test_perception_detection_contract.py tests/test_shape_detection_eval.py tests/test_shape_detection_vertical_lines.py tests/test_shape_detection_classification.py tests/test_shape_detection_colors.py -q`
- Ergebnis:
  - Exit `0`
  - `9 passed in 0.66s`
- Befehl:
  - `PYENV_VERSION=3.10.20 PYTHONPATH=vendor/linux-py310/site-packages:. timeout 300 python -m pytest -q -rs`
- Ergebnis:
  - Exit `0`
  - `620 passed, 5 warnings in 7.36s`

## 4) Fazit

PF1 ist abgeschlossen: Linien-, Kreis- und Rechteckkandidaten besitzen jetzt ein
gemeinsames, reportbares Zwischenformat. Der nächste sinnvolle Schritt ist PF2:
Horizontalstrich-/Minus-Erkennung mit ROI-Hinweis auf Basis dieses Contracts.
