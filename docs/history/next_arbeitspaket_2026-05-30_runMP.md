# Nächstes Arbeitspaket – Run MP (2026-05-30)

Dieses Arbeitspaket arbeitet nach Run MO die nächste dokumentierte
Perception-First-Aufgabe **PF2** ab: Horizontalstrich-/Minus-Erkennung mit
Beschreibungshinweis auf eine Region of Interest. Damit wird der PF1-Contract
nicht nur für generische Primitive genutzt, sondern kann aus Text wie
`oben mittig ist ein "-"-Zeichen` einen konkreten `HorizontalRule`-Seed-Kandidaten
ableiten.

## 1) Nächste dokumentierte Aufgabe: PF2 Minus-/HorizontalRule-Erkennung mit ROI

- Anlass:
  - `docs/open_tasks.md` markierte nach PF1 als nächsten sinnvollen Schritt PF2.
  - `docs/perception_first_task_backlog_2026-05-30.md` fordert für PF2, Hinweise
    wie `oben mittig` vor der ersten Iteration in einen `HorizontalRule`- oder
    `TextGlyph("-")`-Kandidaten zu übersetzen.
- Umsetzung:
  - `tools/shape_detection.py` enthält nun `HorizontalRuleDetection` und
    `detect_horizontal_rules(...)`; die Heuristik sucht dunkle, horizontal
    elongierte Konturen optional innerhalb einer ROI.
  - `tools/perception_detection_contract.py` ergänzt
    `description_hint_to_roi(...)`, `detect_minus_candidates(...)` und
    `make_horizontal_rule_candidate(...)`.
  - Der serialisierte PF1/PF2-Contract nutzt `kind="horizontal_rule"` und führt
    die später für Geometry-IR relevanten Felder `text_equivalent="-"`,
    `geometry_ir_kind="HorizontalRule"`, Position, Länge, Strichstärke, Farbe,
    Confidence, ROI und Evidence mit.

## 2) Gekoppelte Plan-B-/Repro-Aufgabe: synthetisch plus echtes Bild

- Synthetischer Repro:
  - `tools/shape_detection_eval.py` kann nun ein `minus`-Fixture erzeugen.
  - Beschreibung: `oben mittig ist ein "-"-Zeichen`.
  - Ergebnis: ein `horizontal_rule`-Kandidat mit Top-Center-ROI.
- Realbild-Repro:
  - Bild: `artifacts/images_to_convert/AC0120_L.jpg`.
  - Beschreibungshinweis: oben auf der vertikalen Symmetrieachse werden ein
    `+`- und ein `-`-Zeichen eingefügt.
  - Ergebnis: ein `horizontal_rule`-Kandidat bei `bbox=(15,17,10,3)` mit
    `confidence=0.7467`.
- Artefakt:
  - `artifacts/evaluation/perception_minus_roi_v1/perception_minus_roi_report_v1.json`
  - Summary: `samples=2`, `all_matched=true`.

## 3) Sichernde Tests und Checks

- Befehl:
  - `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/test_perception_minus_roi.py tests/test_perception_detection_contract.py`
- Ergebnis:
  - Exit `0`
  - `5 passed in 0.38s`
- Befehl:
  - `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/perception_detection_contract.py --report minus-roi --output-dir artifacts/evaluation/perception_minus_roi_v1`
- Ergebnis:
  - Exit `0`
  - JSON-Summary mit `samples=2` und `all_matched=true`.
- Befehl:
  - `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/test_perception_minus_roi.py tests/test_perception_detection_contract.py tests/test_shape_detection_eval.py tests/test_shape_detection_vertical_lines.py tests/test_shape_detection_classification.py tests/test_shape_detection_colors.py`
- Ergebnis:
  - Exit `0`
  - `12 passed in 0.46s`
- Befehl:
  - `PYENV_VERSION=3.10.20 PYTHONPATH=vendor/linux-py310/site-packages:. timeout 300 python -m pytest -q -rs`
- Ergebnis:
  - Exit `0`
  - `623 passed, 5 warnings in 4.92s`

## 4) Fazit

PF2 ist abgeschlossen: Beschreibungshinweise auf eine obere mittige Region
werden nun in eine ROI übersetzt, dort als horizontale Minus-/Rule-Kontur erkannt
und als `horizontal_rule`-/`HorizontalRule`-Kandidat im gemeinsamen
Perception-Contract protokolliert. Der nächste sinnvolle Schritt laut Backlog ist
PF6: Perception-Telemetrie früh als Report sichtbar machen, bevor PF3/PF4 die
Kandidaten in den Runtime-Fallback integrieren.
