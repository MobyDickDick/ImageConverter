# Nächstes Arbeitspaket – GE9012_6M Fine-Opacity-Probes Run UI (2026-07-01)

Run UI rotiert nach dem SE0041_1-Rule-Stroke-Width-Schritt aus Run UH zum
nächstpriorisierten aktiven Plan-B-Kandidaten `GE9012_6M`. Der Fokus bleibt
katalogfrei: Für die BackBottom-/Light-Grey-Square-Geometrien ergänzt der
Geometry-IR-Optimierer feinere Opacity-Probes für rechteckige Füll- und
Konturelemente.

## 1) Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt für `ColorPatch`- und
  `RectBorder`-Elemente zusätzlich zu den vorhandenen groben Opacity-Stufen nun
  feine Zwischenwerte `0.925` und `0.975`.
- Die neuen Probes gelten gleichermaßen für `fill_opacity` und `stroke_opacity`
  und werden wie alle Elementprobes nur übernommen, wenn der gerenderte Fehler
  im Elementschritt strikt sinkt.
- Die Änderung ist deterministisch und katalogfrei; sie koppelt weder an
  `GE9012_6M` noch an eine andere Runtime-Bild-ID.

## 2) Perception-Lerneffekt

`GE9012_6M` bleibt `nur Sonderfall` auf Ebene des initialen
BackBottom-/hellgraues-Quadrat-Contracts. Run UI erweitert nicht die
Bilddetektion, sondern den allgemeinen Optimierungsraum für bereits vorhandene
`ColorPatch`-/`RectBorder`-Primitive, wie sie aus neutralen Rechteck- und
Füllflächenbeschreibungen entstehen.

## 3) Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_color_patch_opacity_with_fine_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rect_border_stroke_opacity_with_fine_probe` läuft grün mit `2 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün und bestätigt weiterhin `0` Runtime-ID-Vorkommen.

## 4) Ergebnis / nächster Schritt

Run UI schließt den dokumentierten GE9012_6M-Feinschritt ab. Rechteckige
Füll- und Konturelemente können nun katalogfrei feinere Opacity-Varianten
bewerten. Das nächste Arbeitspaket kann in der aktiven Plan-B-Rotation zu
`GE9013_1M` wechseln oder weitere allgemeine Rect-/ColorPatch-Feinparameter
untersuchen.
