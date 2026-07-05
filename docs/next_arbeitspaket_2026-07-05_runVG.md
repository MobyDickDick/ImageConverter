# Nächstes Arbeitspaket – DLG0021 Nanofine-Stroke-Gradient-Offset-Probes Run VG (2026-07-05)

Run VG greift nach Run UZ den optionalen allgemeinen Gradient-Feinschritt auf
und bleibt beim aktiven Plan-B-Kandidaten `DLG0021`. Der Fokus bleibt
katalogfrei: `PolygonPath`-Konturen mit `stroke_gradient` erhalten zusätzliche
nanofeine Offset-Probes, um grüne Haken-/Konturgradienten noch feiner gegen das
Antialiasing-Raster bewerten zu können.

## 1) Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt für `PolygonPath`-Elemente mit
  `stroke_gradient.stops[*].offset` zusätzlich zu den vorhandenen Offset-
  Varianten nun nanofeine `0.0015625`-Schritte.
- Prozent-Offsets nutzen weiterhin die stabile Prozentformatierung mit bis zu
  vier Nachkommastellen, sodass Zwischenwerte wie `50.15625%` verlustfrei als
  SVG-Probe weitergereicht werden.
- Die Änderung ist deterministisch und katalogfrei; sie koppelt weder an
  `DLG0021` noch an eine andere Runtime-Bild-ID.

## 2) Perception-Lerneffekt

`DLG0021` bleibt `nur Sonderfall`: Die reine Bilddetektion liefert weiterhin
keinen stabilen generischen Checkbox-/Checkmark-Seed. Run VG erweitert aber den
allgemeinen Optimierungsraum für vorhandene `PolygonPath`-Stroke-Gradienten,
wie sie aus neutral beschriebenen Haken- und Konturpfaden entstehen.

## 3) Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_stroke_gradient_offsets_with_nanofine_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_stroke_gradient_offsets_with_microfine_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_stroke_gradient_offsets_with_ultrafine_probe` läuft grün mit `3 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün und bestätigt weiterhin `0` Runtime-ID-Vorkommen.
- `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-dlg0021-runVG --start DLG0021 --end DLG0021 --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; die isolierte DLG0021-Metrik bleibt stabil bei `Mean-Delta²=17056.199219` und `Fehler/Pixel=0.077702`.

## 4) Ergebnis / nächster Schritt

Run VG schließt den dokumentierten DLG0021-Gradient-Feinschritt ab.
`PolygonPath`-Stroke-Gradient-Offsets können nun katalogfrei nanofeine
Zwischenlagen bewerten; der isolierte DLG0021-Einzellauf bleibt metrisch stabil.
Das nächste Arbeitspaket kann in der aktiven Plan-B-Rotation zu `GE1410_L`
wechseln oder weitere allgemeine PolygonPath-Antialiasing-/Gradient-Probes
untersuchen.
