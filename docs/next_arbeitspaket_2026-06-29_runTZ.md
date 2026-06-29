# Nächstes Arbeitspaket – DLG0021 Checkmark-Gradient-Probes Run TZ (2026-06-29)

Run TZ arbeitet das nächste dokumentierte Plan-B-Farb-/Pixel-Feintuning für den
weiterhin höchstpriorisierten Kandidaten `DLG0021` aus `PLAN_B_KANDIDATEN.md`
ab. Nach den vorhandenen Punkt-, Stroke-, Linecap-/Linejoin- und Opacity-Probes
fehlte noch eine neutrale Möglichkeit, mehrfarbige `PolygonPath`-Strokes ohne
Katalog-ID anhand ihrer Gradient-Stops zu variieren.

## 1) Umsetzung

- Der generische Geometry-IR-Optimizer nutzt die bestehende neutrale Grau-/Grün-
  Stroke-Palette nun auch für `stroke_gradient.stops[*].color` von
  `PolygonPath`-Elementen.
- Die Probe bleibt katalogfrei: Sie hängt ausschließlich an `PolygonPath` und
  einem vorhandenen `stroke_gradient`-Contract, nicht an Dateinamen oder
  Bild-IDs.
- Die Palette enthält zusätzlich eine helle grüne Zwischenfarbe, damit weiche
  Haken-/Antialiasing-Ränder wie bei `DLG0021` ohne Spezialpfad getestet werden
  können.

## 2) Perception-Lerneffekt

`DLG0021` bleibt `nur Sonderfall`: Die reine Bilddetektion liefert weiterhin
keinen stabilen generischen Checkbox-/Checkmark-Seed. Der ausführbare Pfad ist
weiterhin der katalogfreie Beschreibungspfad mit `ColorPatch`, `RectBorder` und
`PolygonPath`; Run TZ erweitert daran nur den allgemeinen Gradient-Fit.

## 3) Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_stroke_gradient_stops` läuft grün mit `1 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py tests/detailtests/test_description_contract_helpers.py::test_geometry_ir_renderer_emits_checkmark_stroke_gradient` läuft grün mit `21 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün und bestätigt weiterhin `0` Runtime-ID-Vorkommen.

## 4) Ergebnis / nächster Schritt

Das nächste dokumentierte DLG0021-Farb-/Pixel-Paket ist umgesetzt, ohne neue
Runtime-Bild-ID-Abhängigkeiten einzuführen. Das nächste Paket kann den isolierten
DLG0021-Lauf erneut gegen die neuen Gradient-Probes messen oder in der Rotation
zu `GE1410_L` beziehungsweise `SE0041_1` wechseln.
