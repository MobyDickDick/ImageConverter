# Nächstes Arbeitspaket – SE0041_1 Subfine-Rule-Stroke-Width-Probes Run UM (2026-07-02)

Run UM rotiert nach dem GE1410_L-PolygonPath-Feinschritt zurück auf den
aktiven Plan-B-Kandidaten `SE0041_1`. Der Fokus bleibt katalogfrei: die bereits
vorhandenen feinen `HorizontalRule`-/`VerticalRule`-Stroke-Width-Probes werden
um eine noch feinere absolute Stufe ergänzt, damit Square-Badge-Arme und -Stem
antialiasing-sensitiver bewertet werden können.

## 1) Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt für `RectBorder`,
  `HorizontalRule` und `VerticalRule` zusätzlich zu den vorhandenen absoluten
  ±0,005-Stroke-Width-Schritten nun auch ±0,0025.
- Die Probes gelten für alle entsprechenden Geometry-IR-Elemente und werden wie
  alle Elementprobes nur übernommen, wenn der gerenderte Fehler im Elementschritt
  strikt sinkt.
- Die Änderung ist deterministisch und katalogfrei; sie koppelt weder an
  `SE0041_1` noch an eine andere Runtime-Bild-ID.

## 2) Perception-Lerneffekt

`SE0041_1` bleibt ein beschreibungsbasierter Square-Badge-Sonderfall aus der
AC0811-Aliasbeschreibung. Run UM erweitert nicht die reine Bilddetektion,
sondern den allgemeinen Optimierungsraum für bereits vorhandene Rule- und
RectBorder-Konturen.

## 3) Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_vertical_rule_stroke_width_with_subfine_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_horizontal_rule_stroke_width_with_subfine_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_vertical_rule_stroke_width_with_fine_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_horizontal_rule_stroke_width_with_fine_probe` läuft grün mit `4 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün und bestätigt weiterhin `0` Runtime-ID-Vorkommen.
- `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-se0041-runUM --start SE0041_1 --end SE0041_1 --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; die isolierte SE0041_1-Metrik bleibt stabil bei `Mean-Delta²=2436.707764` und `Fehler/Pixel=0.015932`.

## 4) Ergebnis / nächster Schritt

Run UM schließt den dokumentierten SE0041_1-Feinschritt ab. Rule- und
RectBorder-Stroke-Widths können nun katalogfrei feinere absolute Varianten
bewerten; der isolierte SE0041_1-Einzellauf bleibt stabil. Das nächste
Arbeitspaket kann in der aktiven Plan-B-Rotation zu `GE9012_6M` wechseln oder
weiteres allgemeines Badge-/Rect-Antialiasing-Feintuning untersuchen.
