# Nächstes Arbeitspaket – FP-D9 Run NT (2026-06-04)

## Ziel

FP-D9 setzt die zweite AC08-Semantik-Fokusfamilie um: **Plain-Ring `AC0800_*`**.
Die Familie soll `Kreis ohne Buchstabe` aus der Familienregel ableiten, auch
wenn für einen isolierten Variantentest kein XML-Beschreibungstext vorhanden ist.
Zusätzlich soll eine Familienkonsistenzmetrik im Report protokolliert werden.

## Gegenmaßnahme

Der Description-Contract bricht bekannte semantische Familien nicht mehr vor der
Familienregel ab. Für `AC0800_L`, `AC0800_M` und `AC0800_S` wird dadurch bei
fehlendem Beschreibungstext zuerst die AC08-Familienregel ausgewertet:

- `mode=semantic_badge`,
- `label=""`,
- `semantic_sources.family_rule=["SEMANTIC: Kreis ohne Buchstabe"]`,
- `semantic_sources.description_heuristic=[]`,
- `contract_status=family_rule`.

Damit bleibt die Plain-Ring-Semantik explizit aus der Familie abgeleitet und
nicht aus einer weichen Textheuristik.

## Familienkonsistenzmetrik

Der Harmonization-Report schreibt zusätzlich
`family_consistency_metrics.csv` mit:

- `base`,
- `variants`,
- `prototype_group`,
- `intra_family_max_delta`,
- `prototype_max_delta`,
- `variant_count`.

Der AC0800-Fokus-Repro protokollierte:

```text
AC0800;AC0800_L|AC0800_M|AC0800_S;ac08_plain_ring_scale;0.0333;0.0000;3
```

## Sicherung

| Check | Befehl | Exit | Ergebnis |
| --- | --- | ---: | --- |
| Fokus-Regression | `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/test_image_composite_converter.py::test_parse_description_marks_ac0800_as_plain_ring_family tests/test_image_composite_converter.py::test_detect_semantic_primitives_detects_plain_ring_without_arm tests/test_image_composite_converter.py::test_finalize_ac0800_preserves_plain_ring_geometry_bounds tests/test_image_composite_converter.py::test_finalize_ac0800_small_variant_keeps_template_radius_floor tests/detailtests/test_semantic_harmonization_helpers.py` | `0` | `11 passed in 2.30s`; AC0800-Familienregel und neue Metrikdatei sind regressionsgesichert. |
| AC0800-Repro | `timeout 180 env PYTHONPATH=vendor/linux-py310/site-packages:. PYENV_VERSION=3.10.20 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --output-dir /tmp/ic-fpd9-ac0800 --start AC0800 --end AC0800 --deterministic-order` | `0` | Alle drei Varianten liefen als `SEMANTIC: Kreis ohne Buchstabe`; Metrik unter `artifacts/converted_images/reports/FP_D9_family_consistency_metrics_2026-06-04_runNT.csv`. |

## Ergebnis

- FP-D9-1 ist erfüllt: `AC0800_L/M/S` werden ohne Beschreibungstext aus der
  Familienregel als Plain-Ring klassifiziert.
- FP-D9-2 ist erfüllt: Die Familienkonsistenzmetrik wird als CSV protokolliert
  und im AC0800-Repro abgelegt.
- FP-D9-EXIT ist erfüllt: Der Regressionsschutz für die zweite Fokusfamilie ist
  grün und der Fokus-Repro endet mit Exit `0`.

## 5-Zeilen-Log

- **Getestet:** AC0800-Parse-/Primitive-/Finalization-Regressionen,
  Harmonization-Detailtests und AC0800-Fokus-Repro.
- **Ergebnis:** Fokus-Regression `11 passed`; AC0800-Batch Exit `0`;
  `prototype_max_delta=0.0000` in der Plain-Ring-Skalengruppe.
- **Blocker:** Kein FP-D9-Blocker.
- **Nächster Schritt:** FP-D10 prüft eine familienübergreifende
  Harmonisierungshypothese aus `docs/ac08_improvement_plan.md` datenbasiert.
- **Morgiger Startbefehl:** `PYTHONPATH=vendor/linux-py310/site-packages:. PYENV_VERSION=3.10.20 timeout 300 python -m pytest -q -rs`.
