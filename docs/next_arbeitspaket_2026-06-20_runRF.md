# Nächstes Arbeitspaket – IDO-17 Valve-Head-Compatibility-De-ID Run RF (2026-06-20)

Run RF setzt IDO-17 aus `docs/image_description_only_tasks.md` fort und
entfernt die verbliebene katalogspezifische Valve-Head-Kompatibilitätsweiche aus
dem Badge-SVG-Renderer.

## 1) Ziel

Valve-Head-Badges sollen weiterhin ihre dedizierte Kopfgeometrie und den kurzen
zentrierten vertikalen Connector behalten, aber nur noch über neutrales
Style-Metadatum beschrieben werden. Sparse Legacy-Parameter dürfen im
SVG-Renderer nicht mehr anhand eines konkreten Katalogpräfixes repariert werden.

## 2) Umsetzung

- `generateBadgeSvgImpl(...)` wertet keine `variant_name`-/`badge_symbol_name`-/
  `base_name`-Katalogreferenz mehr aus, um `head_style` nachträglich zu setzen.
- Die Valve-Head-Geometrie bleibt ausschließlich an das neutrale Metadatum
  `head_style=ac0223_triple_valve` gekoppelt.
- Zwei Kommentare in Optimierungs-/Quantisierungspfaden wurden auf neutrale
  Valve-Head-Beschreibungen umgestellt, damit der Runtime-ID-Ratchet auch diese
  Vorkommen abbaut.
- Die Legacy-Baseline wurde auf den neuen Runtime-Bestand aktualisiert.

## 3) Nachweis

- `python -m compileall -q src tests/detailtests/test_semantic_badge_svg_helpers.py`
  → Exit `0`.
- `pytest -q tests/detailtests/test_semantic_badge_svg_helpers.py tests/test_image_composite_converter.py::test_make_badge_params_supports_ac0223_valve_head tests/test_image_composite_converter.py::test_generate_badge_svg_renders_ac0223_valve_head_gradient tests/test_image_composite_converter.py::test_quantize_badge_params_keeps_ac0223_top_stem_span`
  → `9 passed`.
- `python tools/check_no_new_image_id_hardcoding.py`
  → `PASS: no image-ID hardcoding above legacy baseline (304 legacy occurrences remain).`

## 4) Ergebnis

IDO-17 baut die Legacy-Baseline weiter ab: Der Badge-SVG-Pfad enthält keine
katalogspezifische Valve-Head-Kompatibilitätsweiche mehr; der Ratchet sinkt von
307 auf 304 Runtime-ID-Vorkommen.

## 5) Nächster Schritt

IDO-17 fortsetzen und die nächsten verbleibenden katalogspezifischen Runtime-
Tokens in Badge-Parametrisierung, Bestlist-Reparatur, Template-Transfer oder
Diagnosepfaden durch neutrale Beschreibungssignale, Parameter oder Testdaten
ersetzen.
