# Nächstes Arbeitspaket – IDO-21 End-to-End-Holdout-Abnahme Run SK (2026-06-24)

Run SK arbeitet nach IDO-19 und IDO-20 das nächste dokumentierte Arbeitspaket aus `docs/image_description_only_tasks.md` ab: **IDO-21 – End-to-End-Holdout-Abnahme durchführen**.

## Änderungen

- Neues Tool `tools/run_end_to_end_holdout_acceptance.py` erzeugt den versionierten Report `end_to_end_holdout_acceptance_v1`.
- Die Abnahme verbindet das IDO-04-Holdout-/Rename-Protokoll, die IDO-19-Ablationsmatrix und das IDO-20-Qualitäts-/Komplexitätsgate.
- Ausgewertet werden nur Holdout-Zeilen im kombinierten `image_and_description`-Modus; die Runtime-Zeilen verwenden ausschließlich anonymisierte `holdout_...`-Evaluationsnamen.
- Jede Zeile protokolliert Source-Contributions, Qualitätsgate-Ergebnis und einen `fusion_uncertainty_v1`-Status. Die Akzeptanz verlangt bestandene Rename-Invarianz, bestandenes Qualitätsgate, keine Review-Pflicht und keine Holdout-/Katalogtoken-Leckage.
- Regressionstests sichern das maschinenlesbare Format, die Leckagefreiheit sowie Qualitäts-/Unsicherheitsakzeptanz.

## Artefakte

- `artifacts/evaluation/end_to_end_holdout_acceptance_v1/end_to_end_holdout_acceptance_v1.json`

## Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/test_end_to_end_holdout_acceptance.py` läuft grün.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/run_end_to_end_holdout_acceptance.py` läuft grün und meldet `accepted=true`.
- `python tools/check_no_new_image_id_hardcoding.py` meldet weiterhin `0` Runtime-ID-Vorkommen.

## Ergebnis

IDO-21 ist abgeschlossen: Die End-to-End-Holdout-Abnahme ist automatisiert, nutzt katalogfreie Holdout-Namen, besteht Qualitätsgate und Unsicherheitskalibrierung und prüft maschinenlesbar, dass keine zurückgehaltenen Originalnamen oder Katalogtokens in den Abnahmezeilen auftauchen.
