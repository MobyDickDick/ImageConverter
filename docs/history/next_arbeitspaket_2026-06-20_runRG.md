# Nächstes Arbeitspaket – IDO-17 Valve-Head-Neutralisierung Run RG (2026-06-20)

Run RG setzt IDO-17 aus `docs/image_description_only_tasks.md` fort und baut
verbliebene katalogspezifische Runtime-Tokens im Valve-Head-Bereich ab, ohne die
in Run RF stabilisierte Legacy-Kompatibilität zu entfernen.

## 1) Ziel

Valve-Head-Badges bleiben über neutrales `head_style=ac0223_triple_valve`
steuerbar. Dokumentations- und SVG-interne Marker im Runtime-Code sollen keine
katalogartige Bild-ID mehr tragen, damit der Ratchet weiter sinkt und neue
Rendererpfade katalogfrei benannt werden.

## 2) Umsetzung

- Der SVG-Gradient für Valve-Head-Geometrie heißt nun `valveHeadGradient` statt
  katalogspezifisch benannt zu sein.
- Die zugehörigen Detail- und Regressionstests prüfen den neuen neutralen
  Gradient-Identifier.
- Die Valve-Head-Hilfsmodul-Docstrings und Kommentare wurden auf neutrale
  Top-Connector-/Valve-Head-Beschreibungen umgestellt.
- Die Legacy-Baseline wurde auf den neuen Runtime-Bestand aktualisiert.

## 3) Nachweis

- `python -m compileall -q src/iCCModules/imageCompositeConverterSemanticAc0223.py src/iCCModules/imageCompositeConverterSemanticBadgeSvg.py tests/detailtests/test_semantic_badge_svg_helpers.py tests/detailtests/test_ac0223_semantic_helpers.py tests/test_image_composite_converter.py`
  → Exit `0`.
- `pytest -q tests/detailtests/test_semantic_badge_svg_helpers.py tests/detailtests/test_ac0223_semantic_helpers.py tests/test_image_composite_converter.py::test_generate_badge_svg_renders_ac0223_valve_head_gradient`
  → `14 passed`.
- `python tools/check_no_new_image_id_hardcoding.py`
  → `PASS: no image-ID hardcoding above legacy baseline (295 legacy occurrences remain).`

## 4) Ergebnis

IDO-17 reduziert den Runtime-ID-Ratchet von `302` auf `295` Vorkommen. Die
Valve-Head-Geometrie bleibt weiterhin über neutrales Style-Metadatum und die in
Run RF abgesicherte sparse Legacy-Weiche erreichbar; neu sichtbare SVG-Marker
sind katalogfrei benannt.

## 5) Nächster Schritt

IDO-17 fortsetzen: verbleibende katalogspezifische Runtime-Tokens in
Badge-Parametrisierung, Bestlist-Reparatur, Template-Transfer, Diagnosepfaden
und semantischen Familienmodulen weiter durch neutrale Beschreibungssignale,
Parameter oder Testdaten ersetzen. Die Valve-Head-Kompatibilitätsweiche erst
entfernen, wenn alle Aufrufer zuverlässig neutrales `head_style` liefern.
