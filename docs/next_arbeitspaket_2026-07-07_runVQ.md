# Nächstes Arbeitspaket – GE9013_1M Picofine-Warmfill-Probe Run VQ (2026-07-07)

Run VQ rotiert nach dem GE9012_6M-Femtofine-Opacity-Schritt aus Run VP zum
aktiven Plan-B-Kandidaten `GE9013_1M`. Der Fokus bleibt katalogfrei: Die
allgemeinen warmen `ColorPatch`-/`RectBorder`-Füllfarb-Probes erhalten eine
zusätzliche picofeine Zwischenfarbe für die rötlich-warme BackBottom-
Quadratfamilie.

## 1) Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt für rechteckige Füllflächen
  zusätzlich die warme Zwischenfarbe `#f2b9b7`.
- Der neue Wert ergänzt die vorhandenen Nachbarwerte `#f2b9b6` und `#f2bab6`
  und wird wie alle Elementprobes nur übernommen, wenn der gerenderte Fehler im
  Elementschritt strikt sinkt.
- Die Änderung ist deterministisch und katalogfrei; sie koppelt weder an
  `GE9013_1M` noch an eine andere Runtime-Bild-ID.

## 2) Perception-Lerneffekt

`GE9013_1M` bleibt auf Ebene des initialen BackBottom-/hellgraues-Quadrat-
Contracts ein `nur Sonderfall`-Signal. Run VQ erweitert nicht die Bilddetektion,
sondern den allgemeinen Optimierungsraum für bereits vorhandene rechteckige
`ColorPatch`-/`RectBorder`-Primitive, die aus neutralen Rechteck- und
Füllflächenbeschreibungen entstehen.

## 3) Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rect_to_picofine_warm_light_fill tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rect_to_nanofine_warm_light_fill tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rect_to_subfine_warm_light_fill tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rect_to_fine_warm_light_fill` läuft grün mit `4 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün und bestätigt weiterhin `0` Runtime-ID-Vorkommen.

## 4) Ergebnis / nächster Schritt

Run VQ schließt den dokumentierten GE9013_1M-Feinschritt ab. Rechteckige
Füllflächen können nun katalogfrei die zusätzliche warme Zwischenfarbe bewerten;
der nächste Plan-B-Schritt kann in der aktiven Rotation zu `DLG0021` wechseln
oder weiteres allgemeines Rect-/ColorPatch-Feintuning prüfen.
