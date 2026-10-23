# Nächstes Arbeitspaket – GE9013_1M Subpixel-BBox-Probes Run UJ (2026-07-01)

Run UJ rotiert nach dem GE9012_6M-Fine-Opacity-Schritt aus Run UI zum
nächstpriorisierten aktiven Plan-B-Kandidaten `GE9013_1M`. Der Fokus bleibt
katalogfrei: Für die schmale BackBottom-/Light-Grey-Square-Variante ergänzt der
Geometry-IR-Optimierer feinere Bounding-Box-Probes für rechteckige Füll- und
Konturelemente.

## 1) Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt für `ColorPatch`- und
  `RectBorder`-Elemente zusätzlich zu den vorhandenen Kanten-Nudges nun auch
  sehr feine ±0,0025-BBox-Schritte.
- Die neuen Probes gelten für alle vier `bbox`-Koordinaten und werden wie alle
  Elementprobes nur übernommen, wenn der gerenderte Fehler im Elementschritt
  strikt sinkt.
- Die Änderung ist deterministisch und katalogfrei; sie koppelt weder an
  `GE9013_1M` noch an eine andere Runtime-Bild-ID.

## 2) Perception-Lerneffekt

`GE9013_1M` bleibt `nur Sonderfall` auf Ebene des initialen
BackBottom-/hellgraues-Quadrat-Contracts und der vertikalen Canvas-Skalierung.
Run UJ erweitert nicht die Bilddetektion, sondern den allgemeinen
Optimierungsraum für bereits vorhandene `ColorPatch`-/`RectBorder`-Primitive,
wie sie aus neutralen Rechteck- und Füllflächenbeschreibungen entstehen.

## 3) Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_color_patch_bbox_with_subpixel_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rect_border_bbox_with_subpixel_probe` läuft grün mit `2 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün und bestätigt weiterhin `0` Runtime-ID-Vorkommen.
- `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ge9013-runUJ --start GE9013_1M --end GE9013_1M --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; die isolierte GE9013_1M-Metrik bleibt stabil bei `Mean-Delta²=12989.524414` und `Fehler/Pixel=0.035766`.

## 4) Ergebnis / nächster Schritt

Run UJ schließt den dokumentierten GE9013_1M-Feinschritt ab. Rechteckige Füll-
und Konturelemente können nun katalogfrei feinere BBox-Varianten bewerten. Das
nächste Arbeitspaket kann in der aktiven Plan-B-Rotation zu `DLG0021` wechseln
oder weitere allgemeine Rect-/ColorPatch-Feinparameter untersuchen.
