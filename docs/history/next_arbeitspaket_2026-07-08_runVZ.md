# Nächstes Arbeitspaket – SE0041_1 Yoctofine-Rule-Stroke-Probes Run VZ (2026-07-08)

Run VZ rotiert nach dem GE1410_L-Yoctofine-PolygonPath-Schritt aus Run VY zum
aktiven Plan-B-Kandidaten `SE0041_1`. Der Fokus bleibt katalogfrei: Die bereits
allgemeinen `RectBorder`-, `HorizontalRule`- und `VerticalRule`-Stroke-Width-
Probes werden um eine noch feinere yoctofeine absolute Stufe ergänzt, damit
Square-Badge-Konturen und Stem-/Arm-Linien minimale Antialiasing-Kantenlagen
bewerten können.

## 1) Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt für `RectBorder`,
  `HorizontalRule` und `VerticalRule` jetzt zusätzlich yoctofeine absolute
  `stroke_width`-Deltas von `±0.00001953125`.
- Die neue Stufe liegt zwischen dem unveränderten Ausgangswert und der bereits
  vorhandenen zeptofeinen Stufe `±0.0000390625`; sie wird wie alle
  Elementprobes nur übernommen, wenn der gerenderte Fehler im Elementschritt
  strikt sinkt.
- Die Änderung ist deterministisch und katalogfrei; sie koppelt weder an
  `SE0041_1` noch an eine andere Runtime-Bild-ID.

## 2) Perception-Lerneffekt

`SE0041_1` bleibt auf Ebene der reinen Bilddetektion ein `nur Sonderfall`-
Signal. Run VZ erweitert nicht die Detektion, sondern den allgemeinen
Optimierungsraum für bereits vorhandene rechteckige Konturen und horizontale
oder vertikale Regeln, die aus neutralen Beschreibungs- oder Perception-Seeds
entstehen.

## 3) Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rect_border_stroke_width_with_yoctofine_absolute_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rule_stroke_width_with_yoctofine_absolute_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rule_stroke_width_with_zeptofine_absolute_probe` läuft grün mit `3 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün und bestätigt weiterhin `0` Runtime-ID-Vorkommen.
- `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-se0041-runVZ --start SE0041_1 --end SE0041_1 --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; der isolierte SE0041_1-Einzellauf bleibt stabil bei `Mean-Delta²=2436.707764` und `Fehler/Pixel=0.015932`.

## 4) Ergebnis / nächster Schritt

Run VZ schließt den dokumentierten SE0041_1-Feinschritt ab. Rechteckige
Konturen und Rule-Strokes können nun katalogfrei yoctofeine Breitenvarianten
bewerten; der isolierte SE0041_1-Einzellauf bleibt metrisch stabil. Das nächste
Arbeitspaket kann in der aktiven Plan-B-Rotation zu `GE9012_6M` wechseln oder
weiteres allgemeines Rect-/Rule-Antialiasing-Feintuning prüfen.
