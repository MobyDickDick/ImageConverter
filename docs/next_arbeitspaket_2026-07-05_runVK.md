# Nächstes Arbeitspaket – DLG0021 Picofine-Stroke-Gradient-Offset-Probes Run VK (2026-07-05)

Run VK rotiert nach `docs/next_arbeitspaket_2026-07-05_runUY.md` zurück auf den
aktiven Plan-B-Kandidaten `DLG0021`. Der Fokus bleibt katalogfrei: Die bereits
allgemeinen `PolygonPath`-Stroke-Gradient-Offset-Probes werden um eine picofeine
Zwischenstufe erweitert, damit schmale Checkmark-/Schatten-Gradienten noch
kleinere Stop-Verschiebungen bewerten können.

## 1) Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt für `PolygonPath`-Elemente mit
  `stroke_gradient.stops[*].offset` zusätzlich zu den vorhandenen 0,15625-
  Prozentpunkt-Schritten nun auch picofeine 0,078125-Prozentpunkt-Schritte.
- Die neuen Probes gelten neutral für alle prozentualen Stroke-Gradient-Stops und
  werden wie alle Elementprobes nur übernommen, wenn der gerenderte Fehler im
  Elementschritt strikt sinkt.
- Die Änderung ist deterministisch und katalogfrei; sie koppelt weder an
  `DLG0021` noch an eine andere Runtime-Bild-ID.

## 2) Perception-Lerneffekt

`DLG0021` bleibt auf Ebene des initialen Checkbox-/Haken-Contracts ein
`nur Sonderfall`-Signal. Run VK erweitert nicht die Bilddetektion, sondern den
allgemeinen Optimierungsraum für bereits vorhandene `PolygonPath`-Konturen mit
Stroke-Gradienten, die aus neutralen Polygon-/Pfadbeschreibungen entstehen.

## 3) Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_stroke_gradient_offsets_with_picofine_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_stroke_gradient_offsets_with_nanofine_probe` läuft grün mit `2 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün und bestätigt weiterhin `0` Runtime-ID-Vorkommen.
- `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-dlg0021-runVK --start DLG0021 --end DLG0021 --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; die isolierte DLG0021-Metrik bleibt stabil bei `Mean-Delta²=17056.199219` und `Fehler/Pixel=0.077702`.

## 4) Ergebnis / nächster Schritt

Run VK schließt den dokumentierten DLG0021-Feinschritt ab. Stroke-Gradient-
Konturen können nun katalogfrei picofeine Offset-Varianten bewerten. Das nächste
Arbeitspaket kann in der aktiven Plan-B-Rotation weiter zu `GE1410_L` wechseln
oder optional weiteres allgemeines Antialiasing-/Gradienten-Feintuning prüfen.
