# Nächstes Arbeitspaket – IDO-17 Connector-Free-Badge-SVG-De-ID Run RD (2026-06-20)

Run RD setzt IDO-17 aus `docs/image_description_only_tasks.md` fort und entfernt
die verbliebene katalogspezifische Connector-Free-Badge-Liste aus dem
SVG-Renderer.

## 1) Ziel

Connectorfreie Kreis-/Text-Badges sollen weiterhin stale Arm-/Stem-Geometrie aus
Optimierungs- oder Transferproben verwerfen, aber nicht mehr über konkrete
Katalog-Symbol-IDs im Runtime-SVG-Pfad erkannt werden.

## 2) Umsetzung

- `generateBadgeSvgImpl(...)` entscheidet die Connector-Unterdrückung jetzt über
  neutrales Geometrie-Metadatum `connector_policy=forbid` oder den expliziten
  Parameter `suppress_stale_connector_geometry`.
- Die bisherige SVG-seitige Liste connectorfreier AC08-Symbol-IDs wurde entfernt.
- Der Detailtest nutzt einen neutralen VOC-Badge-Namen und prüft weiterhin, dass
  stale Arm-Geometrie nicht gerendert wird.
- Die Legacy-Baseline wurde auf den neuen Runtime-Bestand aktualisiert.

## 3) Nachweis

- `python -m compileall -q src tests/detailtests/test_semantic_badge_svg_helpers.py`
  → Exit `0`.
- `pytest -q tests/detailtests/test_semantic_badge_svg_helpers.py`
  → `5 passed`.
- `pytest -q tests/test_image_composite_converter.py::test_make_badge_params_ac0835_uses_plain_voc_circle_geometry tests/test_image_composite_converter.py::test_reflection_routes_connector_free_rh_badge_to_geometry_ir`
  → `2 passed`.
- `python tools/check_no_new_image_id_hardcoding.py`
  → `PASS: no image-ID hardcoding above legacy baseline (308 legacy occurrences remain).`
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/review_conversion_quality.py`
  → `diff_renderable_pairs=630`, `successful_renderable_pairs=48`, `selected=GE9002_7S,GE9002_5S,GE9002_3S,GE9002_4M,GE9002_1S`.

## 4) Ergebnis

IDO-17 baut die Legacy-Baseline weiter ab: Der Badge-SVG-Pfad enthält keine
connectorfreie AC08-Symbol-ID-Liste mehr; der Ratchet sinkt von 314 auf 308
Runtime-ID-Vorkommen.

## 5) Nächster Schritt

IDO-17 fortsetzen und die nächsten verbleibenden katalogspezifischen Runtime-
Tokens in Badge-Parametrisierung, Finalisierung, Fitting oder Diagnosepfaden
durch neutrale Beschreibungssignale, Parameter oder Testdaten ersetzen.
