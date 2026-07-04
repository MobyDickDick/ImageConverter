# Nächstes Arbeitspaket – GE1410_L Nanofine-PolygonPath-Point-Probes Run VA (2026-07-04)

Run VA rotiert nach `docs/next_arbeitspaket_2026-07-04_runUZ.md` auf den
aktiven Plan-B-Kandidaten `GE1410_L`. Der Fokus bleibt katalogfrei: Die
bestehenden `PolygonPath`-Punktprobes für Diagramm-Dreiecke erhalten eine
nanofeine Subpixel-Stufe, damit rote/blaue Dreiecksspitzen und Kanten noch
präziser gegen Antialiasing-Rasterlagen getestet werden können.

## 1) Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt für `PolygonPath.points[*][x|y]`
  zusätzlich zu den vorhandenen Schrittweiten nun nanofeine `0.0003125`-
  Subpixel-Offsets in beide Richtungen.
- Die Änderung ist deterministisch und katalogfrei; sie koppelt weder an
  `GE1410_L` noch an eine andere Runtime-Bild-ID.
- Ein Detailtest sichert die neue Kandidatenstufe explizit gegen Regression ab.

## 2) Perception-Lerneffekt

`GE1410_L` bleibt `generalisiert`: Achsen-/Linien- und Dreieck-Seeds werden
bereits als katalogfreie Geometry-IR-Elemente abgeleitet. Run VA verfeinert
diesen allgemeinen Diagrammpfad nur im lokalen `PolygonPath`-Punkt-Suchraum,
ohne eine bildspezifische Sonderregel einzuführen.

## 3) Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_points_with_nanofine_subpixel_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_points_with_microfine_subpixel_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_points_with_ultrafine_subpixel_probe` läuft grün mit `3 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün und bestätigt weiterhin `0` Runtime-ID-Vorkommen.
- `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ge1410-runVA --start GE1410_L --end GE1410_L --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; die isolierte GE1410_L-Metrik bleibt stabil bei `Mean-Delta²=759.441589` und `Fehler/Pixel=0.010179`.

## 4) Ergebnis / nächster Schritt

Run VA schließt den dokumentierten GE1410_L-Feinschritt ab. `PolygonPath`-
Dreieckspunkte können nun katalogfrei nanofeine Zwischenlagen bewerten; der
isolierte GE1410_L-Einzellauf bleibt metrisch stabil. Das nächste Arbeitspaket
kann in der aktiven Plan-B-Rotation zu `SE0041_1` wechseln oder weitere
allgemeine PolygonPath-Antialiasing-/Stroke-Feintuning-Probes untersuchen.
