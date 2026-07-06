# Nächstes Arbeitspaket – GE1410_L Femtofine-PolygonPath-Probes Run VL (2026-07-05)

Run VL rotiert nach `docs/next_arbeitspaket_2026-07-05_runVK.md` in der
aktiven Plan-B-Liste weiter zu `GE1410_L`. Der Fokus bleibt katalogfrei: Die
allgemeinen `PolygonPath`-Feinprobes werden um eine femtofeine Zwischenstufe
erweitert, damit kleine Diagramm-/Dreieckskonturen und ihre Antialiasing-Kanten
noch kleinere Punkt- und Konturbreitenverschiebungen bewerten können.

## 1) Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt für `PolygonPath`-Elemente nun
  zusätzlich femtofeine absolute `stroke_width`-Deltas von `±0.000078125`.
- Dieselbe femtofeine Schrittweite wird für lokale `PolygonPath.points`-
  Koordinatenprobes ergänzt.
- Die neuen Probes gelten neutral für alle Polygonpfade und werden wie alle
  Elementprobes nur übernommen, wenn der gerenderte Fehler im Elementschritt
  strikt sinkt.
- Die Änderung ist deterministisch und katalogfrei; sie koppelt weder an
  `GE1410_L` noch an eine andere Runtime-Bild-ID.

## 2) Perception-Lerneffekt

`GE1410_L` bleibt für Achsen-/Linien- und Dreieck-Seeds `generalisiert`. Run VL
erweitert nicht die initiale Bilddetektion, sondern den allgemeinen
Optimierungsraum für bereits erkannte oder beschreibungsbasierte
`PolygonPath`-Diagrammprimitive.

## 3) Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_points_with_femtofine_subpixel_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_points_with_picofine_subpixel_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_stroke_width_with_picofine_absolute_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_stroke_width_with_femtofine_absolute_probe` läuft grün mit `4 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün und bestätigt weiterhin `0` Runtime-ID-Vorkommen.
- `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ge1410-runVL --start GE1410_L --end GE1410_L --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; die isolierte GE1410_L-Metrik bleibt stabil bei `Mean-Delta²=759.441589` und `Fehler/Pixel=0.010179`.

## 4) Ergebnis / nächster Schritt

Run VL schließt den dokumentierten GE1410_L-Feinschritt ab. Polygonpfade können
nun katalogfrei femtofeine Punkt- und Konturbreitenvarianten bewerten. Das
nächste Arbeitspaket kann in der aktiven Plan-B-Rotation weiter zu `SE0041_1`
wechseln oder optional weiteres allgemeines Antialiasing-Feintuning prüfen.
