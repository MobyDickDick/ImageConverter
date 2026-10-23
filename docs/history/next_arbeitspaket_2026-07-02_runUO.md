# Nächstes Arbeitspaket – GE9012_6M Ultrafine-Opacity-Probes Run UO (2026-07-02)

Run UO rotiert nach dem SE0041_1-Rule-/RectBorder-Feinschritt zurück auf den
aktiven Plan-B-Kandidaten `GE9012_6M`. Der Fokus bleibt katalogfrei: die bereits
vorhandenen `ColorPatch`-/`RectBorder`-Opacity-Probes werden um noch feinere
Zwischenstufen ergänzt, damit hellgraue BackBottom-Flächen und Konturen in der
allgemeinen Geometry-IR-Optimierung rasterempfindlicher bewertet werden können.

## 1) Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt für `ColorPatch` und
  `RectBorder` zusätzlich zu den vorhandenen Opacity-Stufen in 0,0125er-Schritten
  nun weitere 0,00625er-Zwischenstufen im oberen Opacity-Bereich.
- Die neuen Stufen gelten gleichermaßen für `fill_opacity` und `stroke_opacity`.
- Die Änderung ist deterministisch und katalogfrei; sie koppelt weder an
  `GE9012_6M` noch an eine andere Runtime-Bild-ID.

## 2) Perception-Lerneffekt

`GE9012_6M` bleibt ein beschreibungsbasierter BackBottom-/hellgraues-Quadrat-
Sonderfall. Run UO erweitert nicht die reine Bilddetektion, sondern den
allgemeinen Optimierungsraum für bereits vorhandene Rechteck- und Farbflächen-
Konturen.

## 3) Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_color_patch_opacity_with_ultrafine_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rect_border_stroke_opacity_with_ultrafine_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_color_patch_opacity_with_subfine_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rect_border_stroke_opacity_with_subfine_probe` läuft grün mit `4 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün und bestätigt weiterhin `0` Runtime-ID-Vorkommen.
- `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ge9012-runUO --start GE9012_6M --end GE9012_6M --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; die isolierte GE9012_6M-Metrik bleibt stabil bei `Mean-Delta²=15386.639648` und `Fehler/Pixel=0.044122`.

## 4) Ergebnis / nächster Schritt

Run UO schließt den dokumentierten GE9012_6M-Feinschritt ab. `ColorPatch`- und
`RectBorder`-Opacities können nun katalogfrei feinere Zwischenstufen bewerten;
der isolierte GE9012_6M-Einzellauf bleibt stabil. Das nächste Arbeitspaket kann
in der aktiven Plan-B-Rotation zu `GE9013_1M` wechseln oder weiteres allgemeines
Rechteck-/BackBottom-Antialiasing-Feintuning untersuchen.
