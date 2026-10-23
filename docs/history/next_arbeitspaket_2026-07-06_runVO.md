# Nächstes Arbeitspaket – SE0041_1 Attofine-Rule-Stroke-Probes Run VO (2026-07-06)

Run VO rotiert nach dem GE1410_L-Attofine-PolygonPath-Schritt aus Run VN zum
aktiven Plan-B-Kandidaten `SE0041_1`. Der Fokus bleibt katalogfrei: Die
allgemeinen `RectBorder`-, `HorizontalRule`- und `VerticalRule`-`stroke_width`-
Probes werden um eine attofeine absolute Zwischenstufe erweitert, damit
Square-Badge-Konturen und Rule-Stems noch kleinere Antialiasing-Abweichungen
bewerten können.

## 1) Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt für `RectBorder`,
  `HorizontalRule` und `VerticalRule` zusätzlich attofeine absolute
  `stroke_width`-Deltas von `±0.000078125`.
- Die neue Zwischenstufe ergänzt die vorhandenen picofeinen `±0.00015625`-
  Probes und wird wie alle Elementprobes nur übernommen, wenn der gerenderte
  Fehler im Elementschritt strikt sinkt.
- Die Änderung ist deterministisch und katalogfrei; sie koppelt weder an
  `SE0041_1` noch an eine andere Runtime-Bild-ID.

## 2) Perception-Lerneffekt

`SE0041_1` bleibt auf Ebene des initialen Square-Badge-Seeds ein
`nur Sonderfall`-Signal. Run VO erweitert nicht die Bilddetektion, sondern den
allgemeinen Optimierungsraum für bereits beschreibungsbasiert erzeugte
Rechteckkonturen und horizontale beziehungsweise vertikale Rule-Elemente.

## 3) Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rect_border_stroke_width_with_attofine_absolute_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rule_stroke_width_with_attofine_absolute_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rule_stroke_width_with_picofine_absolute_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rect_border_stroke_width_with_fine_probe` läuft grün mit `4 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün und bestätigt weiterhin `0` Runtime-ID-Vorkommen.
- `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-se0041-runVO --start SE0041_1 --end SE0041_1 --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; der isolierte SE0041_1-Einzellauf bleibt stabil bei `Mean-Delta²=2436.707764` und `Fehler/Pixel=0.015932`.

## 4) Ergebnis / nächster Schritt

Run VO schließt den dokumentierten SE0041_1-Feinschritt ab. Rechteckkonturen
sowie horizontale und vertikale Rule-Elemente können nun katalogfrei attofeine
absolute Stroke-Width-Varianten bewerten; der isolierte SE0041_1-Einzellauf
bleibt stabil. Das nächste Arbeitspaket kann in der aktiven Plan-B-Rotation zu
`GE9012_6M` wechseln oder weiteres allgemeines Antialiasing-Feintuning prüfen.
