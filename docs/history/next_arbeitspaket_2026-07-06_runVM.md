# Nächstes Arbeitspaket – DLG0021 Femtofine-Gradient-Offset-Probes Run VM (2026-07-06)

Run VM rotiert nach dem GE9013_1M-Picofine-BBox-Schritt aus Run UY zurück zum
aktiven Plan-B-Kandidaten `DLG0021`. Der Fokus bleibt katalogfrei: Die bereits
allgemeinen `PolygonPath.stroke_gradient.stops[*].offset`-Probes werden um eine
femtofeine Zwischenstufe erweitert, damit Checkmark-/Konturverläufe noch kleinere
Gradientenverschiebungen bewerten können.

## 1) Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt für `PolygonPath`-Elemente mit
  `stroke_gradient.stops` zusätzlich femtofeine Offset-Deltas von `±0.000390625`
  in normalisierten Koordinaten, also `±0.0390625` Prozentpunkte.
- Die neue Zwischenstufe ergänzt die vorhandenen gröberen Offset-Probes bis hin
  zu `±0.00078125` und wird wie alle Elementprobes nur übernommen, wenn der
  gerenderte Fehler im Elementschritt strikt sinkt.
- Die Änderung ist deterministisch und katalogfrei; sie koppelt weder an
  `DLG0021` noch an eine andere Runtime-Bild-ID.

## 2) Perception-Lerneffekt

`DLG0021` bleibt auf Ebene des initialen Checkbox-/Haken-Contracts ein
`nur Sonderfall`-Signal. Run VM erweitert nicht die Bilddetektion, sondern den
allgemeinen Optimierungsraum für bereits beschreibungsbasiert erzeugte
`PolygonPath`-Gradientenkonturen.

## 3) Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_stroke_gradient_offsets_with_femtofine_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_stroke_gradient_offsets_with_picofine_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_stroke_gradient_offsets_with_nanofine_probe` läuft grün mit `3 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün und bestätigt weiterhin `0` Runtime-ID-Vorkommen.
- `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-dlg0021-runVM --start DLG0021 --end DLG0021 --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; die isolierte DLG0021-Metrik bleibt stabil bei `Mean-Delta²=17056.199219` und `Fehler/Pixel=0.077702`.

## 4) Ergebnis / nächster Schritt

Run VM schließt den dokumentierten DLG0021-Feinschritt ab. `PolygonPath`-
Stroke-Gradienten können nun katalogfrei femtofeine Offset-Varianten bewerten;
der isolierte DLG0021-Einzellauf bleibt stabil. Das nächste Arbeitspaket kann in
der aktiven Plan-B-Rotation zu `GE1410_L` wechseln oder weiteres allgemeines
Gradienten-/Kontur-Feintuning prüfen.
