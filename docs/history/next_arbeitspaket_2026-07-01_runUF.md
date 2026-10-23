# Nächstes Arbeitspaket – DLG0021 feine Stroke-Gradient-Offset-Probes Run UF (2026-07-01)

Run UF rotiert nach dem GE9013_1M-Stroke-Width-Schritt aus Run UE wieder auf
`DLG0021` aus der aktiven Plan-B-Liste. Der Fokus bleibt katalogfrei: Der
Geometry-IR-Optimierer erhält feinere `PolygonPath`-Stroke-Gradient-Offset-
Probes, damit beschriebene Haken-/Konturpfade kleine Antialiasing- und
Gradientenlage-Abweichungen ohne Bild-ID-Sonderfall bewerten können.

## 1) Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt für `PolygonPath`-Elemente mit
  `stroke_gradient.stops[*].offset` zusätzlich feine ±2,5-Prozentpunkte.
- Die neuen Probes ergänzen die vorhandenen ±5- und ±10-Prozentpunkte und werden
  wie alle Kandidaten nur übernommen, wenn der gerenderte Fehler strikt sinkt.
- Die Änderung ist elementweise, deterministisch und katalogfrei; sie koppelt
  weder an `DLG0021` noch an eine andere Runtime-Bild-ID.

## 2) Perception-Lerneffekt

`DLG0021` bleibt `nur Sonderfall` auf Ebene des beschreibungsbasierten
Checkbox-/Haken-Contracts. Run UF erweitert nicht die initiale Bilddetektion,
sondern den allgemeinen Optimierungsraum für vorhandene `PolygonPath`-
Gradientpfade: Sobald ein Gradient-Stroke im Geometry-IR-Pfad vorliegt, kann
eine feinere Stop-Lage ohne Katalogbindung bewertet werden.

## 3) Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_stroke_gradient_offsets tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_stroke_gradient_offsets_with_fine_probe` läuft grün mit `2 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün und bestätigt weiterhin `0` Runtime-ID-Vorkommen.
- `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-dlg0021-runUF --start DLG0021 --end DLG0021 --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; die isolierte DLG0021-Metrik bleibt stabil bei `Mean-Delta²=17056.199219` und `Fehler/Pixel=0.077702`.

## 4) Ergebnis / nächster Schritt

Run UF schließt den dokumentierten DLG0021-Feinschritt ab. `PolygonPath`-
Gradient-Strokes können nun katalogfrei feinere Offset-Varianten optimieren; der
isolierte DLG0021-Einzellauf bleibt stabil. Das nächste Arbeitspaket kann in der
aktiven Plan-B-Rotation zu `GE1410_L` wechseln oder weiteres allgemeines
Gradient-/Antialiasing-Feintuning untersuchen.
