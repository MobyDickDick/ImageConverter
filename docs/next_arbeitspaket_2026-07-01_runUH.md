# Nächstes Arbeitspaket – SE0041_1 Rule-Stroke-Width-Probes Run UH (2026-07-01)

Run UH rotiert nach dem GE1410_L-Stroke-Width-Schritt aus Run UG zum
nächstpriorisierten aktiven Plan-B-Kandidaten `SE0041_1` zurück. Der Fokus bleibt
katalogfrei: Für die antialiasing-sensitiven horizontalen und vertikalen Badge-
Connectoren ergänzt der Geometry-IR-Optimierer feine absolute
`stroke_width`-Probes.

## 1) Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt für `HorizontalRule`- und
  `VerticalRule`-Elemente zusätzlich zu den vorhandenen relativen
  Stroke-Width-Varianten nun auch feine absolute ±0,005-Schritte.
- Die neuen Probes entsprechen den bereits für `RectBorder` und `PolygonPath`
  genutzten kleinen Antialiasing-Schritten und werden nur übernommen, wenn der
  gerenderte Fehler im Elementschritt strikt sinkt.
- Die Änderung ist deterministisch und katalogfrei; sie koppelt weder an
  `SE0041_1` noch an eine andere Runtime-Bild-ID.

## 2) Perception-Lerneffekt

`SE0041_1` bleibt `nur Sonderfall` auf Ebene der initialen Square-Badge-Seed-
Annahme. Run UH erweitert nicht die Bilddetektion, sondern den allgemeinen
Optimierungsraum für bereits vorhandene `HorizontalRule`-/`VerticalRule`-
Primitive, wie sie aus neutralen Badge-Connector-Beschreibungen entstehen.

## 3) Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_vertical_rule_stroke_width_with_fine_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_horizontal_rule_stroke_width_with_fine_probe` läuft grün mit `2 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün und bestätigt weiterhin `0` Runtime-ID-Vorkommen.
- `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-se0041-runUH --start SE0041_1 --end SE0041_1 --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; die isolierte SE0041_1-Metrik bleibt stabil bei `Mean-Delta²=2436.707764` und `Fehler/Pixel=0.015932`.

## 4) Ergebnis / nächster Schritt

Run UH schließt den dokumentierten SE0041_1-Feinschritt ab. Rule-Connectoren
können nun katalogfrei feinere absolute Stroke-Width-Varianten bewerten; der
isolierte SE0041_1-Einzellauf bleibt stabil. Das nächste Arbeitspaket kann in
der aktiven Plan-B-Rotation zu `GE9012_6M` wechseln oder weiteres allgemeines
Rect-/Rule-Antialiasing-Feintuning untersuchen.
