# Nächstes Arbeitspaket – SE0041_1 Nanofine-Rule-Stroke-Probes Run UW (2026-07-03)

Run UW rotiert nach dem GE1410_L-PolygonPath-Feinschritt zurück zum aktiven
Plan-B-Kandidaten `SE0041_1`. Der Fokus bleibt katalogfrei: Die bestehenden
`HorizontalRule`-/`VerticalRule`-Stroke-Width-Probes erhalten einen noch feineren
lokalen Absolutschritt, damit Square-Badge-Stem- und Arm-Kanten pixelnäher
registriert werden können.

## 1) Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt für `RectBorder`,
  `HorizontalRule` und `VerticalRule` zusätzlich zu den vorhandenen lokalen
  Stroke-Width-Varianten nun nanofeine `0.0003125`-Absolutschritte.
- Die neuen Probes gelten neutral für regel- und rechteckbasierte IR-Elemente
  und werden wie alle Elementprobes nur übernommen, wenn der gerenderte Fehler
  im Elementschritt strikt sinkt.
- Die Änderung ist deterministisch und katalogfrei; sie koppelt weder an
  `SE0041_1` noch an eine andere Runtime-Bild-ID.

## 2) Perception-Lerneffekt

`SE0041_1` bleibt für den Square-Badge-Seed ein beschreibungsbasierter
Sonderfall. Run UW erweitert nicht die reine Bilddetektion, sondern den
allgemeinen Optimierungsraum für vorhandene Rule-/RectBorder-Stroke-Konturen,
wie sie aus neutral beschriebenen eckigen Badge-Formen entstehen.

## 3) Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rule_stroke_width_with_nanofine_absolute_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rule_stroke_width_with_microfine_absolute_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_vertical_rule_stroke_width_with_ultrafine_probe` läuft grün mit `3 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün und bestätigt weiterhin `0` Runtime-ID-Vorkommen.
- `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-se0041-runUW --start SE0041_1 --end SE0041_1 --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; die isolierte SE0041_1-Metrik bleibt stabil bei `Mean-Delta²=2436.707764` und `Fehler/Pixel=0.015932`.

## 4) Ergebnis / nächster Schritt

Run UW schließt den dokumentierten SE0041_1-Feinschritt ab. Rule- und
RectBorder-Stroke-Breiten können nun katalogfrei nanofeine Absolutvarianten
bewerten; der isolierte SE0041_1-Einzellauf bleibt metrisch stabil. Das nächste
Arbeitspaket kann in der aktiven Plan-B-Rotation zu `GE9012_6M` wechseln oder
weitere allgemeine Kanten-/Antialiasing-Feinregistrierung untersuchen.
