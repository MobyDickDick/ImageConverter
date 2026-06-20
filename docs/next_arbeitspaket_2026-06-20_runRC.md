# Nächstes Arbeitspaket – IDO-17 Geometry-IR-Self-Reference-De-ID Run RC (2026-06-20)

Run RC setzt IDO-17 aus `docs/image_description_only_tasks.md` fort und
entfernt die verbliebene katalogspezifische Self-Reference-Formulierung aus dem
beschreibungsgetriebenen Geometry-IR-Pfad.

## 1) Ziel

Rechteck-/Plus-/Minus-Self-Reference-Beschreibungen sollen weiterhin eine
explizite Rect-/Diagonal-/Glyph-Kette erzeugen, aber nicht mehr über eine
konkrete Katalog-ID im Runtime-Code erkannt werden.

## 2) Umsetzung

- `buildGeometryIrFromDescriptionImpl(...)` erkennt die Self-Reference jetzt über
  den neutralen Beschreibungstoken `rechteck-plus-minus-bildbeschreibung`.
- Der bisherige katalogspezifische Token wurde aus Rect-Hint und
  Diagonalentscheidung entfernt.
- Der zugehörige Detailtest verwendet eine katalogfreie Beschreibung und einen
  neutralen Testnamen, prüft aber weiterhin dieselbe Plus-/Minus-/Diagonal-Kette.

## 3) Nachweis

- `python -m compileall -q src tests/detailtests/test_geometry_ir_helpers.py`
  → Exit `0`.
- `pytest -q tests/detailtests/test_geometry_ir_helpers.py::test_build_geometry_ir_maps_neutral_self_description_to_plus_minus_chain`
  → `1 passed`.
- `pytest -q tests/detailtests/test_geometry_ir_helpers.py`
  → `55 passed`.
- `python tools/check_no_new_image_id_hardcoding.py`
  → `PASS: no image-ID hardcoding above legacy baseline (314 legacy occurrences remain).`

## 4) Ergebnis

IDO-17 baut die Legacy-Baseline weiter ab: Der Geometry-IR-Self-Reference-Pfad
enthält keine konkrete Runtime-Katalog-ID mehr; der Ratchet sinkt von 316 auf
314 Runtime-ID-Vorkommen.

## 5) Nächster Schritt

IDO-17 fortsetzen und die nächsten verbleibenden katalogspezifischen Runtime-
Tokens in Beschreibungs-, Finalisierungs- oder Diagnosepfaden durch neutrale
Beschreibungssignale, Parameter oder Testdaten ersetzen.
