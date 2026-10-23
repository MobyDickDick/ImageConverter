# Nächstes Arbeitspaket – IDO-07 Perception-IR-Roundtrip Run QA (2026-06-16)

## Ziel

Run QA bearbeitet das nächste offene Arbeitspaket aus
`docs/image_description_only_tasks.md`: **IDO-07 – Perception-Kandidaten
vollständig auf dieselbe IR abbilden**. Der vorhandene
`perception_primitive_candidate_v1`-Contract soll für die unterstützten
Primitive-Typen ohne Bild-/Katalog-ID in renderbare Geometry-IR-Seeds übersetzt
werden.

## Umsetzung

- `merge_perception_candidates_into_geometry_ir(...)` mappt jetzt zusätzlich
  vertikale/horizontale Linien, Polygon-/Pfad-Kandidaten, Text-Glyphen bzw.
  Textbereiche und Farbfeld-Kandidaten in generische Geometry-IR-Elemente.
- Perception-Seeds tragen einheitliche Confidence-, Source-, Detector- und
  Evidence-Metadaten weiter; bestehende Kreis/Ring-, Rechteck- und
  HorizontalRule-Seeds bleiben kompatibel.
- Der Geometry-IR-Renderer unterstützt nun generische `PolygonPath`- und
  `ColorPatch`-Elemente, damit neu abgebildete Perception-Kandidaten ohne
  Spezialrenderer als SVG roundtrip-fähig sind.
- Neue synthetische Regressionen verwenden neutrale Kandidatenquellen und prüfen
  für Kreis/Ring, Linie, Rechteck, Polygon, Pfad, Text-Glyph, Textbereich und
  Farbe jeweils Serialisierung, Geometry-IR-Seed und SVG-Renderbarkeit.

## Laufzeit- und Akzeptanznachweis

```bash
python -m compileall -q src tools tests/test_perception_geometry_ir_roundtrip.py && python tools/check_no_new_image_id_hardcoding.py && pytest -q tests/test_perception_geometry_ir_roundtrip.py tests/test_perception_detection_contract.py tests/test_perception_seeded_geometry_ir.py
```

Ergebnis: Exit `0`; der Ratchet bleibt auf der bestehenden Legacy-Baseline, und
`tests/test_perception_geometry_ir_roundtrip.py`,
`tests/test_perception_detection_contract.py` sowie
`tests/test_perception_seeded_geometry_ir.py` laufen zusammen mit `13 passed`.

## 5-Zeilen-Log

- **Getestet:** Perception-Contract → Geometry-IR → SVG-Roundtrip für alle IDO-07-Primitive.
- **Ergebnis:** Exit `0`; `13 passed` im gezielten Perception-/IR-Testblock.
- **Blocker:** Kein neuer Blocker; IDO-08 bleibt als nächster P1-Fusionsschritt offen.
- **Dokumentation:** IDO-07 ist in `docs/image_description_only_tasks.md` abgeschlossen und dieser Run hält den Nachweis fest.
- **Nächster Schritt:** IDO-08 umsetzen: Beschreibungs-Constraints und Bildkandidaten generisch über gewichtete Kosten/Wahrscheinlichkeiten fusionieren.
