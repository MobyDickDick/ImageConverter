# Nächstes Arbeitspaket – IDO-19 Ablationsmatrix Run SI (2026-06-24)

Run SI arbeitet nach Abschluss von IDO-18 das nächste dokumentierte Arbeitspaket aus `docs/image_description_only_tasks.md` ab: **IDO-19 – Ablationsmatrix automatisieren**.

## Umsetzung

- Neues Tool `tools/build_holdout_ablation_matrix.py` erzeugt den versionierten Report `holdout_ablation_matrix_v1`.
- Der Report verwendet den IDO-04-Holdout-/Rename-Vertrag und wertet jeden Sample in drei Modi aus: `image_only`, `description_only` und `image_and_description`.
- Jede Reportzeile dokumentiert, welche Constraints aus Bild- beziehungsweise Beschreibungsquelle stammen.
- Die Summary weist getrennt für Development und Holdout aus, dass der kombinierte Modus die Single-Source-Modi nach der definierten Gesamtmetrik übertrifft.

## Artefakte

- `artifacts/evaluation/holdout_ablation_matrix_v1/holdout_ablation_matrix_v1.json`

## Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/test_holdout_ablation_matrix.py tests/test_holdout_rename_protocol.py`
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py`
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/build_holdout_ablation_matrix.py`

## Nächster Schritt

IDO-20 umsetzen: Qualitäts- und Komplexitätsgate für Rasterähnlichkeit, Kantenlage, Struktur, Semantik, SVG-Elementanzahl und Pfadkomplexität definieren.
