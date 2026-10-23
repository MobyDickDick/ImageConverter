# Nächstes Arbeitspaket – GE9012_6M Microfine-Opacity-Probes Run UT (2026-07-03)

Run UT rotiert nach dem SE0041_1-Rule-Stroke-Feinschritt zurück zum aktiven
Plan-B-Kandidaten `GE9012_6M`. Der Fokus bleibt katalogfrei: Die bestehenden
`ColorPatch`-/`RectBorder`-Opacity-Probes erhalten zusätzliche microfeine
Zwischenstufen, damit helle BackBottom-/Quadrat-Flächen mit partieller
Transparenz ohne Bild-ID-Sonderfall enger bewertet werden können.

## 1) Umsetzung

- Die allgemeine Geometry-IR-Optimierung ergänzt für `ColorPatch`- und
  `RectBorder`-Elemente zusätzliche `0.003125`-Zwischenstufen in der
  Opacity-Palette.
- Die neuen Probes gelten für `fill_opacity` und `stroke_opacity` und werden wie
  alle Elementprobes nur übernommen, wenn der gerenderte Fehler im Elementschritt
  strikt sinkt.
- Die Änderung ist deterministisch und katalogfrei; sie koppelt weder an
  `GE9012_6M` noch an eine andere Runtime-Bild-ID.

## 2) Perception-Lerneffekt

`GE9012_6M` bleibt ein beschreibungsbasierter BackBottom-/hellgraues-Quadrat-
Sonderfall. Run UT erweitert nicht die reine Bilddetektion, sondern den
allgemeinen Optimierungsraum für bereits vorhandene Rechteck- und Farbflächen-
Primitive, wie sie aus neutralen BackBottom-/Quadrat-Beschreibungen entstehen.

## 3) Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_color_patch_opacity_with_microfine_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rect_border_stroke_opacity_with_microfine_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_color_patch_opacity_with_ultrafine_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rect_border_stroke_opacity_with_ultrafine_probe` läuft grün mit `4 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün und bestätigt weiterhin `0` Runtime-ID-Vorkommen.
- `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ge9012-runUT --start GE9012_6M --end GE9012_6M --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; die isolierte GE9012_6M-Metrik bleibt stabil bei `Mean-Delta²=15386.639648` und `Fehler/Pixel=0.044122`.

## 4) Ergebnis / nächster Schritt

Run UT schließt den dokumentierten GE9012_6M-Feinschritt ab. Rechteckige Füll-
und Konturelemente können nun katalogfrei microfeine Opacity-Varianten bewerten.
Das nächste Arbeitspaket kann in der aktiven Plan-B-Rotation zu `GE9013_1M`
wechseln oder weiteres allgemeines Rechteck-/BackBottom-Antialiasing-Feintuning
untersuchen.
