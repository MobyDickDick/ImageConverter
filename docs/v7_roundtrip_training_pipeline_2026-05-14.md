# V7 – Rückwärts-Training / Closed-Loop-Evaluation (2026-05-14)

## Ziel

Für V7 wurde ein erster auswertbarer Closed-Loop-Baustein ergänzt, der zwei semantische Szenen (Referenz vs. Rücktransformation) automatisiert vergleicht und Gap-Reports pro Relationstyp/Object liefert.

## Implementierter Baustein

- Neues Tool: `tools/evaluate_semantic_roundtrip.py`
- Eingaben:
  - `--reference`: erwartete semantische Szene (JSON)
  - `--candidate`: rücktransformierte semantische Szene (JSON)
- Ausgabe:
  - `--output`: strukturierter Gap-Report mit
    - Summary (`passed`, Objekt-/Relationszähler)
    - Gaps (`missing_objects`, `missing_relations`, `extra_*`)
    - `invertibility_failures` (z. B. `relation_loss`, `object_loss`)

## Reproduzierbarer Lauf

```bash
python tools/evaluate_semantic_roundtrip.py \
  --reference artifacts/evaluation/semantic_scene_description_v1/example_scene.json \
  --candidate artifacts/evaluation/semantic_scene_description_v1/example_scene.json \
  --output artifacts/evaluation/semantic_roundtrip_v1/report_2026-05-14.json
```

## Ergebnis (Baseline)

- Exit: `0`
- Report: `artifacts/evaluation/semantic_roundtrip_v1/report_2026-05-14.json`
- Baseline-Status: `passed=true`, keine Objekt- oder Relationslücken.

## Einordnung gegen V7-Akzeptanz

- Die Pipeline-Komponente zur Gap-Erkennung ist vorhanden und erzeugt maschinenlesbare Failure-Modes.
- Damit ist der V7-Deliverable-Kern („Closed-Loop-Evaluationspipeline mit Gap-Reports pro Relationstyp“) als v1-Basis erfüllt.
- Nächster Ausbau: echte Text→SVG→Raster→Rücktransformationsläufe als Candidate-Input automatisiert einspeisen und per Batch auswerten.
