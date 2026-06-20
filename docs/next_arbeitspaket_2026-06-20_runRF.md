# Nächstes Arbeitspaket – IDO-17 Valve-Head-Compatibility-Guard Run RF (2026-06-20)

Run RF setzt IDO-17 aus `docs/image_description_only_tasks.md` fort und
stabilisiert die Valve-Head-Kompatibilität im Badge-SVG-Renderer nach dem
De-ID-Umbau.

## 1) Ziel

Valve-Head-Badges sollen ihre dedizierte Kopfgeometrie und den kurzen
zentrierten vertikalen Connector behalten. Neue Pfade beschreiben dies über das
neutrale Style-Metadatum `head_style=ac0223_triple_valve`; historische sparse
Legacy-Parameter mit bestehender Variant-Referenz müssen bis zur vollständigen
Migration weiterhin sicher gerendert werden.

## 2) Umsetzung

- `generateBadgeSvgImpl(...)` behält eine eng begrenzte Legacy-Kompatibilität:
  Wenn `head_style` fehlt und eine historische Valve-Head-Referenz
  (z. B. Variant-, Symbol-, Base- oder Dateiname) anliegt, wird
  `head_style=ac0223_triple_valve` nachgesetzt.
- Die Valve-Head-Geometrie selbst bleibt weiterhin am neutralen Metadatum
  `head_style=ac0223_triple_valve` gekoppelt.
- Detailtests sichern Legacy-Fälle mit fehlenden Style-Keys und prüfen
  Gradient, Connector-Farbe, Dateiname-Erkennung sowie die Reihenfolge Connector
  vor Kreis.
- Zwei Kommentare in Optimierungs-/Quantisierungspfaden wurden auf neutrale
  Valve-Head-Beschreibungen umgestellt, damit der Runtime-ID-Ratchet diese
  Vorkommen abbaut.
- Die Legacy-Baseline wurde auf den neuen Runtime-Bestand aktualisiert.

## 3) Nachweis

- `python -m compileall -q src tests/detailtests/test_semantic_badge_svg_helpers.py`
  → Exit `0`.
- `pytest -q tests/detailtests/test_semantic_badge_svg_helpers.py tests/test_image_composite_converter.py::test_make_badge_params_supports_ac0223_valve_head tests/test_image_composite_converter.py::test_generate_badge_svg_renders_ac0223_valve_head_gradient tests/test_image_composite_converter.py::test_quantize_badge_params_keeps_ac0223_top_stem_span`
  → `11 passed`.
- `python tools/check_no_new_image_id_hardcoding.py`
  → `PASS: no image-ID hardcoding above legacy baseline (305 legacy occurrences remain).`

## 4) Ergebnis

IDO-17 baut die Legacy-Baseline weiter ab, ohne den dokumentierten sparse
Legacy-Rendererfall zu brechen: Die neutralen Kommentar-Vorkommen wurden
bereinigt, während die notwendige Valve-Head-Kompatibilitätsweiche bis zur
vollständigen Parametermigration abgesichert bleibt.

## 5) Nächster Schritt

IDO-17 fortsetzen und die verbleibende Valve-Head-Kompatibilitätsweiche erst
dann entfernen, wenn alle Aufrufer zuverlässig neutrales `head_style`-Metadatum
liefern. Parallel die nächsten katalogspezifischen Runtime-Tokens in
Badge-Parametrisierung, Bestlist-Reparatur, Template-Transfer oder
Diagnosepfaden durch neutrale Beschreibungssignale, Parameter oder Testdaten
ersetzen.
