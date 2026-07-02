# Nächstes Arbeitspaket – GE9012_6M Subfine-Opacity-Probes Run UN (2026-07-02)

Run UN rotiert nach dem SE0041_1-Rule-Stroke-Feinschritt auf den aktiven
Plan-B-Kandidaten `GE9012_6M`. Der Fokus bleibt katalogfrei: die bereits
vorhandenen `ColorPatch`-/`RectBorder`-Opacity-Probes werden um feinere
Zwischenstufen ergänzt, damit BackBottom-/hellgraue Quadratflächen und ihre
Konturen antialiasing-sensitiver bewertet werden können.

## 1) Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt für `ColorPatch` und
  `RectBorder` zusätzlich zu den vorhandenen Opacity-Stufen nun auch `0.9125`,
  `0.9375`, `0.9625` und `0.9875`.
- Die neuen Probes gelten gleichermaßen für `fill_opacity` und `stroke_opacity`
  und werden wie alle Elementprobes nur übernommen, wenn der gerenderte Fehler
  im Elementschritt strikt sinkt.
- Die Änderung ist deterministisch und katalogfrei; sie koppelt weder an
  `GE9012_6M` noch an eine andere Runtime-Bild-ID.

## 2) Perception-Lerneffekt

`GE9012_6M` bleibt ein beschreibungsbasierter BackBottom-/hellgraues-Quadrat-
Sonderfall. Run UN erweitert nicht die reine Bilddetektion, sondern den
allgemeinen Optimierungsraum für bereits vorhandene rechteckige Flächen- und
Konturelemente.

## 3) Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_color_patch_opacity_with_subfine_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rect_border_stroke_opacity_with_subfine_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_color_patch_opacity_with_fine_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rect_border_stroke_opacity_with_fine_probe` läuft grün mit `4 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün und bestätigt weiterhin `0` Runtime-ID-Vorkommen.
- `ICC_FORCE_RECONVERT=1 PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ge9012-runUN-force --start GE9012_6M --end GE9012_6M --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; die isolierte GE9012_6M-Metrik bleibt stabil bei `Mean-Delta²=15386.639648` und `Fehler/Pixel=0.044122`.

## 4) Ergebnis / nächster Schritt

Run UN schließt den dokumentierten GE9012_6M-Feinschritt ab. Rechteckige
Geometry-IR-Flächen und -Konturen können nun katalogfrei feinere
Opacity-Zwischenstufen bewerten; der isolierte GE9012_6M-Einzellauf bleibt
stabil. Das nächste Arbeitspaket kann in der aktiven Plan-B-Rotation zu
`GE9013_1M` wechseln oder weiteres allgemeines Rect-/BackBottom-Feintuning
untersuchen.
