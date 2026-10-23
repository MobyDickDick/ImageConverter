# Nächstes Arbeitspaket – DLG0021 Ultrafine-Gradient-Offset-Probes Run UQ (2026-07-03)

Run UQ rotiert nach dem GE9013_1M-BBox-Feinschritt zurück zum aktiven Plan-B-
Kandidaten `DLG0021`. Der Fokus bleibt katalogfrei: `PolygonPath`-Konturen mit
Stroke-Gradienten erhalten einen noch feineren lokalen Offset-Suchschritt, damit
bereits erkannte Haken-/Konturverläufe pixelnäher registriert werden können.

## 1) Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt für `PolygonPath`-Elemente mit
  `stroke_gradient.stops[*].offset` zusätzlich zu den vorhandenen Offset-
  Varianten nun ultrafeine `0.00625`-Schritte.
- Die Probes gelten für alle Prozent-Offsets in Stroke-Gradient-Stops und werden
  wie alle Elementprobes nur übernommen, wenn der gerenderte Fehler im
  Elementschritt strikt sinkt.
- Die Änderung ist deterministisch und katalogfrei; sie koppelt weder an
  `DLG0021` noch an eine andere Runtime-Bild-ID.

## 2) Perception-Lerneffekt

`DLG0021` bleibt `nur Sonderfall` auf Ebene des beschreibungsbasierten
Checkbox-/Haken-Primitive-Contracts. Run UQ erweitert nicht die reine
Bilddetektion, sondern den allgemeinen Optimierungsraum für bereits vorhandene
`PolygonPath`-Stroke-Gradienten, wie sie aus neutral beschriebenen Haken- und
Konturprimitiven entstehen.

## 3) Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_stroke_gradient_offsets_with_ultrafine_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_stroke_gradient_offsets_with_subfine_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_stroke_gradient_offsets_with_fine_probe` läuft grün mit `3 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün und bestätigt weiterhin `0` Runtime-ID-Vorkommen.
- `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-dlg0021-runUQ --start DLG0021 --end DLG0021 --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; die isolierte DLG0021-Metrik bleibt stabil bei `Mean-Delta²=17056.199219` und `Fehler/Pixel=0.077702`.

## 4) Ergebnis / nächster Schritt

Run UQ schließt den dokumentierten DLG0021-Feinschritt ab. `PolygonPath`-
Stroke-Gradienten können nun katalogfrei ultrafeine Offset-Varianten bewerten;
der isolierte DLG0021-Einzellauf bleibt stabil. Das nächste Arbeitspaket kann in
der aktiven Plan-B-Rotation zu `GE1410_L` wechseln oder weiteres allgemeines
PolygonPath-Antialiasing-/Gradient-Feintuning untersuchen.
