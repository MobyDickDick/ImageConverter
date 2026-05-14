# V1 Primitive-Inventar v1 – Baseline (2026-05-14)

## Deliverables

- Schema: `docs/vision/primitive_inventory_v1.schema.json`
- Baseline-Testbatch (4 Referenzen):
  - GT: `artifacts/evaluation/primitive_inventory_v1/ground_truth.json`
  - Prediction: `artifacts/evaluation/primitive_inventory_v1/predictions.json`
- Auswertung:
  - Script: `tools/evaluate_primitive_inventory.py`
  - Report: `artifacts/evaluation/primitive_inventory_v1/metrics.json`

## Precision/Recall je Elementtyp

Siehe `metrics.json`; zusammengefasst:

- circle: P=1.00, R=1.00
- ellipse: P=0.50, R=1.00
- line: P=1.00, R=1.00
- path_curve: P=1.00, R=1.00
- polygon: P=1.00, R=1.00
- rect: P=0.00, R=0.00
- text: P=1.00, R=0.50

## Hinweis

Dies ist eine dokumentierte v1-Baseline für Messbarkeit und Schema-Stabilisierung.
