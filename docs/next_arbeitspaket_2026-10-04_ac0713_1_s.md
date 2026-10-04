# Nächstes Arbeitspaket – AC0713_1_S 180°-Quadrat-Kelle (2026-10-04)

## Anlass

Nach Abschluss von ZG7.6 beginnt die Plan-B-Rotation mit `AC0713_1_S`.
Der bisher gespeicherte Lauf fiel trotz der Beschreibung "Kelle, aber mit
Quadrat anstelle von Kreis oben; 180° gedreht" auf einen falschen
Kreis-/Text- bzw. generischen Rechteckpfad zurück. Dadurch lag die Baseline bei
`mean_delta2=24899.021484` und `normalized_mse=0.127638`.

## Änderung

Der Beschreibungspfad erkennt nun katalogfrei die Kombination aus:

- Kelle,
- Quadrat/Viereck statt Kreis,
- 180°-Rotation.

Daraus entsteht eine neue `Rotated180SquareKelleGlyph` mit oberem Connector und
unterem Quadratkörper. Zusätzlich respektiert die freie Semantic-Badge-Heuristik
explizite Square-Kellen-Geometry-IR und überschreibt sie nicht mehr nur wegen
des Beschreibungstexts "Symmetrieachse des Kreises" als Kreis-Badge.

Es wurde keine neue Runtime-Katalog-ID in `src/` ergänzt.

## Ergebnis

Isolierter Recheck:

```text
AC0713_1_S.jpg
output: artifacts/tmp_ac0713_codex_run2
status: non_composite_perception_seeded_geometry_ir
geometry_ir_element_1=CircleBackground
geometry_ir_element_2=Rotated180SquareKelleGlyph
geometry_ir_element_3=OrthogonalPolyline
```

| Metrik | Vorher | Nachher |
|---|---:|---:|
| mean_delta2 | 24899.021484 | 11805.333008 |
| normalized_mse | 0.127638 | ca. 0.06054 |
| spatial_quality_score | 61105.136140 | 34054.345163 |

Der Lauf verbessert die Pixelmetrik deutlich, ist aber noch kein
Satisfaction-Pass. Die Fehler bleiben strukturiert
(`error_energy_concentrated_in_worst_tiles`, `localized_error_fraction=0.773328`).
`AC0713_1_S` bleibt deshalb in der Plan-B-Rotation offen.

## Verifikation

```text
pytest tests/detailtests/test_geometry_ir_helpers.py -k square_kelle
pytest tests/detailtests/test_description_contract_helpers.py -k 180_rotated_square_kelle
pytest tests/detailtests/test_semantic_family_rules_helpers.py -k square_kelle
pytest tests/test_no_new_image_id_hardcoding.py
```

Alle fokussierten Tests waren grün. Die lokale `.venv` ist auf diesem Rechner
defekt; die Tests liefen mit temporär unter `.codex-test-deps` installierten
Abhängigkeiten und isoliertem Python-Start.
