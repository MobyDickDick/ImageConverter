# Nächstes Arbeitspaket – GE9012_6M Femtofine-Opacity-Probes Run VP (2026-07-07)

Run VP rotiert nach dem SE0041_1-Attofine-Rule-Stroke-Schritt aus Run VO zum
aktiven Plan-B-Kandidaten `GE9012_6M`. Der Fokus bleibt katalogfrei: Die
allgemeinen `ColorPatch`-/`RectBorder`-Opacity-Probes werden um femtofeine
Zwischenwerte erweitert, damit BackBottom-/Light-Grey-Square-Flächen und
Konturen noch kleinere Alpha-Abweichungen bewerten können.

## 1) Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt für `ColorPatch`- und
  `RectBorder`-Elemente zusätzlich femtofeine Opacity-Zwischenwerte
  `0.982421875` und `0.983203125`.
- Die neuen Werte ergänzen die vorhandenen picofeinen Nachbarwerte `0.9828125`
  und `0.98359375` und werden wie alle Elementprobes nur übernommen, wenn der
  gerenderte Fehler im Elementschritt strikt sinkt.
- Die Änderung ist deterministisch und katalogfrei; sie koppelt weder an
  `GE9012_6M` noch an eine andere Runtime-Bild-ID.

## 2) Perception-Lerneffekt

`GE9012_6M` bleibt auf Ebene des initialen BackBottom-/hellgraues-Quadrat-
Contracts ein `nur Sonderfall`-Signal. Run VP erweitert nicht die Bilddetektion,
sondern den allgemeinen Optimierungsraum für bereits vorhandene rechteckige
`ColorPatch`-/`RectBorder`-Primitive, die aus neutralen Rechteck- und
Füllflächenbeschreibungen entstehen.

## 3) Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_color_patch_opacity_with_femtofine_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rect_border_stroke_opacity_with_femtofine_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_color_patch_opacity_with_picofine_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rect_border_stroke_opacity_with_picofine_probe` läuft grün mit `4 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün und bestätigt weiterhin `0` Runtime-ID-Vorkommen.
- `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ge9012-runVP --start GE9012_6M --end GE9012_6M --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; der isolierte GE9012_6M-Einzellauf bleibt stabil bei `Mean-Delta²=15386.639648` und `Fehler/Pixel=0.044122`.

## 4) Ergebnis / nächster Schritt

Run VP schließt den dokumentierten GE9012_6M-Feinschritt ab. Rechteckige Füll-
und Konturelemente können nun katalogfrei femtofeine Opacity-Varianten bewerten;
der isolierte GE9012_6M-Einzellauf bleibt metrisch stabil. Das nächste
Arbeitspaket kann in der aktiven Plan-B-Rotation zu `GE9013_1M` wechseln oder
weiteres allgemeines Rect-/ColorPatch-Feintuning prüfen.
