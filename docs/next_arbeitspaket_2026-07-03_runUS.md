# Nächstes Arbeitspaket – SE0041_1 microfeine Rule-Stroke-Probes Run US (2026-07-03)

Run US rotiert nach dem GE1410_L-PolygonPath-Schritt aus Run UR zum aktiven
Plan-B-Kandidaten `SE0041_1`. Der Fokus bleibt katalogfrei: Für den
Square-Badge mit viereckigem Kopf und Strich-/Stem-Geometrie werden die
allgemeinen `RectBorder`-/`HorizontalRule`-/`VerticalRule`-Stroke-Width-Probes
um eine microfeine absolute Stufe erweitert.

## 1) Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt für `RectBorder`,
  `HorizontalRule` und `VerticalRule` zusätzlich zu den vorhandenen lokalen
  Stroke-Width-Schritten nun microfeine `0.000625`-Abweichungen.
- Die neuen Probes gelten neutral für Rechteckkonturen und horizontale bzw.
  vertikale Regeln und werden nur übernommen, wenn der gerenderte Fehler im
  Elementschritt strikt sinkt.
- Die Änderung ist deterministisch und katalogfrei; sie koppelt weder an
  `SE0041_1` noch an eine andere Runtime-Bild-ID.

## 2) Perception-Lerneffekt

`SE0041_1` bleibt ein beschreibungsbasierter Square-Badge-Sonderfall aus der
AC0811-Aliasbeschreibung. Run US erweitert nicht die reine Detektion, sondern
den allgemeinen Optimierungsraum für bereits vorhandene rechteckige Kopf- und
Stem-/Rule-Primitive.

## 3) Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rule_stroke_width_with_microfine_absolute_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_points_with_ultrafine_subpixel_probe` läuft grün mit `2 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün und bestätigt weiterhin `0` Runtime-ID-Vorkommen.
- `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-se0041-runUS --start SE0041_1 --end SE0041_1 --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; die isolierte SE0041_1-Metrik bleibt stabil bei `Mean-Delta²=2436.707764` und `Fehler/Pixel=0.015932`.

## 4) Ergebnis / nächster Schritt

Run US schließt den dokumentierten SE0041_1-Feinschritt ab. Rule- und
RectBorder-Stroke-Widths können nun katalogfrei microfeine Varianten bewerten;
der isolierte SE0041_1-Einzellauf bleibt metrisch stabil. Das nächste
Arbeitspaket kann in der aktiven Plan-B-Rotation zu `GE9012_6M` wechseln oder
weiteres allgemeines Square-Badge-Antialiasing-/Stem-Feintuning untersuchen.
