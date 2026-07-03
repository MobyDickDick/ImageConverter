# Nächstes Arbeitspaket – SE0041_1 Ultrafine-Rule-Stroke-Probes Run US (2026-07-03)

Run US rotiert nach dem GE1410_L-PolygonPath-Punkt-Feinschritt zurück zum
aktiven Plan-B-Kandidaten `SE0041_1`. Der Fokus bleibt katalogfrei: Die
bestehenden `HorizontalRule`-/`VerticalRule`-Stroke-Width-Probes erhalten einen
noch feineren lokalen Schritt, damit kleine Square-Badge-Arme und -Stems
pixelnäher registriert werden können.

## 1) Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt für `HorizontalRule`- und
  `VerticalRule`-Elemente zusätzlich zu den vorhandenen absoluten
  Stroke-Width-Varianten nun ultrafeine `0.00125`-Schritte.
- Die neuen Probes gelten symmetrisch für dünnere und stärkere Linien und werden
  wie alle Elementprobes nur übernommen, wenn der gerenderte Fehler im
  Elementschritt strikt sinkt.
- Die Änderung ist deterministisch und katalogfrei; sie koppelt weder an
  `SE0041_1` noch an eine andere Runtime-Bild-ID.

## 2) Perception-Lerneffekt

`SE0041_1` bleibt ein beschreibungsbasierter Square-Badge-/Rule-Sonderfall. Run
US erweitert nicht die reine Bilddetektion, sondern den allgemeinen
Optimierungsraum für bereits vorhandene horizontale und vertikale
Rule-Primitive, wie sie aus neutral beschriebenen Badge-Armen und -Stems
entstehen.

## 3) Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_vertical_rule_stroke_width_with_ultrafine_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_horizontal_rule_stroke_width_with_ultrafine_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_vertical_rule_stroke_width_with_subfine_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_horizontal_rule_stroke_width_with_subfine_probe` läuft grün mit `4 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün und bestätigt weiterhin `0` Runtime-ID-Vorkommen.

## 4) Ergebnis / nächster Schritt

Run US schließt den dokumentierten SE0041_1-Feinschritt ab. Horizontale und
vertikale Rule-Primitive können nun katalogfrei ultrafeine Stroke-Width-
Varianten bewerten. Das nächste Arbeitspaket kann in der aktiven Plan-B-
Rotation zu `GE9012_6M` wechseln oder weiteres allgemeines Rule-/RectBorder-
Antialiasing-Feintuning untersuchen.
