# Nächstes Arbeitspaket – GE9013_1M Picofine-BBox-Probes Run UY (2026-07-05)

Run UY arbeitet nach dem GE9012_6M-Nanofine-Opacity-Schritt erneut den in der
aktiven Plan-B-Rotation genannten Kandidaten `GE9013_1M` ab. Der Fokus bleibt
katalogfrei: Die bereits allgemeinen `ColorPatch`-/`RectBorder`-BBox-Probes
werden um eine picofeine Zwischenstufe erweitert, damit schmale
BackBottom-/Light-Grey-Square-Rechtecke feinere Kantenverschiebungen bewerten
können.

## 1) Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt für `ColorPatch`- und
  `RectBorder`-Elemente zusätzlich zu den vorhandenen 0,00125er-Subpixel-Schritten
  nun auch picofeine 0,000625er-BBox-Schritte.
- Die neuen Probes gelten neutral für alle vier `bbox`-Koordinaten und werden
  wie alle Elementprobes nur übernommen, wenn der gerenderte Fehler im
  Elementschritt strikt sinkt.
- Die Änderung ist deterministisch und katalogfrei; sie koppelt weder an
  `GE9013_1M` noch an eine andere Runtime-Bild-ID.

## 2) Perception-Lerneffekt

`GE9013_1M` bleibt auf Ebene des initialen BackBottom-/hellgraues-Quadrat-
Contracts ein `nur Sonderfall`-Signal. Run UY erweitert nicht die Bilddetektion,
sondern den allgemeinen Optimierungsraum für bereits vorhandene rechteckige
`ColorPatch`-/`RectBorder`-Primitive, die aus neutralen Rechteck- und
Füllflächenbeschreibungen entstehen.

## 3) Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_color_patch_bbox_with_picofine_subpixel_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rect_border_bbox_with_picofine_subpixel_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_color_patch_bbox_with_subpixel_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rect_border_bbox_with_subpixel_probe` läuft grün mit `4 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün und bestätigt weiterhin `0` Runtime-ID-Vorkommen.
- `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ge9013-runUY --start GE9013_1M --end GE9013_1M --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; die isolierte GE9013_1M-Metrik bleibt stabil bei `Mean-Delta²=12989.524414` und `Fehler/Pixel=0.035766`.

## 4) Ergebnis / nächster Schritt

Run UY schließt den dokumentierten GE9013_1M-Feinschritt ab. Rechteckige Füll-
und Konturelemente können nun katalogfrei picofeine BBox-Varianten bewerten. Das
nächste Arbeitspaket kann in der aktiven Plan-B-Rotation zu `DLG0021` wechseln
oder weitere allgemeine Rect-/ColorPatch-Feinparameter untersuchen.
