# Nächstes Arbeitspaket – GE9013_1M Ultrafine-BBox-Probes Run UP (2026-07-03)

Run UP rotiert nach dem GE9012_6M-Opacity-Feinschritt zurück zum aktiven Plan-B-
Kandidaten `GE9013_1M`. Der Fokus bleibt katalogfrei: Für die schmale
BackBottom-/Light-Grey-Square-Variante ergänzt die allgemeine Geometry-IR-
Optimierung noch feinere Subpixel-Probes an rechteckigen Füll- und
Konturelementen.

## 1) Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt für `ColorPatch`- und
  `RectBorder`-Elemente zusätzlich zu den vorhandenen BBox-Kantenverschiebungen
  nun ultrafeine `0.00125`-Schritte.
- Die neuen Probes gelten für alle vier BBox-Komponenten und werden wie alle
  Elementprobes nur übernommen, wenn der gerenderte Fehler im Elementschritt
  strikt sinkt.
- Die Änderung ist deterministisch und katalogfrei; sie koppelt weder an
  `GE9013_1M` noch an eine andere Runtime-Bild-ID.

## 2) Perception-Lerneffekt

`GE9013_1M` bleibt `nur Sonderfall` auf Ebene des beschreibungsbasierten
BackBottom-/hellgraues-Quadrat-Contracts. Run UP erweitert nicht die reine
Bilddetektion, sondern den allgemeinen Optimierungsraum für bereits vorhandene
`ColorPatch`-/`RectBorder`-Primitive, wie sie aus neutralen Rechteck- und
Füllflächenbeschreibungen entstehen.

## 3) Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_color_patch_bbox_with_ultrafine_subpixel_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rect_border_bbox_with_ultrafine_subpixel_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_color_patch_bbox_with_subpixel_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rect_border_bbox_with_subpixel_probe` läuft grün mit `4 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün und bestätigt weiterhin `0` Runtime-ID-Vorkommen.
- `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ge9013-runUP --start GE9013_1M --end GE9013_1M --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; die isolierte GE9013_1M-Metrik bleibt stabil bei `Mean-Delta²=12989.524414` und `Fehler/Pixel=0.035766`.

## 4) Ergebnis / nächster Schritt

Run UP schließt den dokumentierten GE9013_1M-Feinschritt ab. Rechteckige Füll-
und Konturelemente können nun katalogfrei ultrafeine BBox-Subpixel-Varianten
bewerten; der isolierte GE9013_1M-Einzellauf bleibt stabil. Das nächste
Arbeitspaket kann in der aktiven Plan-B-Rotation zu `DLG0021` wechseln oder
weiteres allgemeines Rechteck-/BackBottom-Antialiasing-Feintuning untersuchen.
