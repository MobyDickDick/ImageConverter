# Nächstes Arbeitspaket – GE1410_L Microfine-PolygonPath-Punktprobes Run UV (2026-07-03)

Run UV rotiert nach dem DLG0021-Gradient-Offset-Feinschritt zurück zum aktiven
Plan-B-Kandidaten `GE1410_L`. Der Fokus bleibt katalogfrei: `PolygonPath`-
Punkte erhalten einen noch feineren lokalen Subpixel-Suchschritt, damit bereits
erkannte Dreiecks-/Diagramm-Primitive pixelnäher registriert werden können.

## 1) Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt für `PolygonPath.points[*][x|y]`
  zusätzlich zu den vorhandenen lokalen Punktvarianten nun microfeine
  `0.000625`-Schritte in beide Richtungen.
- Die Probes gelten für alle `PolygonPath`-Elemente und werden wie alle
  Elementprobes nur übernommen, wenn der gerenderte Fehler im Elementschritt
  strikt sinkt.
- Die Änderung ist deterministisch und katalogfrei; sie koppelt weder an
  `GE1410_L` noch an eine andere Runtime-Bild-ID.

## 2) Perception-Lerneffekt

`GE1410_L` bleibt `generalisiert`: Achsen-/Linien- und Dreieck-Seeds entstehen
aus neutral beschriebenen Diagramm-Primitiven. Run UV erweitert nicht die reine
Bilddetektion, sondern den allgemeinen Optimierungsraum für bereits vorhandene
`PolygonPath`-Punkte.

## 3) Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_points_with_microfine_subpixel_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_points_with_ultrafine_subpixel_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_points_with_subfine_subpixel_probe` läuft grün mit `3 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün und bestätigt weiterhin `0` Runtime-ID-Vorkommen.
- `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ge1410-runUV --start GE1410_L --end GE1410_L --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; die isolierte GE1410_L-Metrik bleibt stabil bei `Mean-Delta²=759.441589` und `Fehler/Pixel=0.010179`.

## 4) Ergebnis / nächster Schritt

Run UV schließt den dokumentierten GE1410_L-Feinschritt ab. `PolygonPath`-
Punkte können nun katalogfrei microfeine Subpixel-Varianten bewerten; der
isolierte GE1410_L-Einzellauf bleibt stabil. Das nächste Arbeitspaket kann in
der aktiven Plan-B-Rotation zu `SE0041_1` wechseln oder weiteres allgemeines
PolygonPath-Antialiasing-/Stroke-Feintuning untersuchen.
