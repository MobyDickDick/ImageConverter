# Nächstes Arbeitspaket – GE9012_6M Picofine-Opacity-Probes Run VC (2026-07-04)

Run VC rotiert nach `docs/next_arbeitspaket_2026-07-04_runVB.md` auf den
aktiven Plan-B-Kandidaten `GE9012_6M`. Der Fokus bleibt katalogfrei: Die
bestehenden `ColorPatch`-/`RectBorder`-Opacity-Probes für helle BackBottom-
Rechteckflächen erhalten picofeine Zwischenwerte, damit sehr kleine
Alpha-Abweichungen zusätzlich gegen das Antialiasing-Raster bewertet werden
können.

## 1) Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt für `ColorPatch` und
  `RectBorder` zusätzlich die picofeinen Opacity-Werte `0.91328125`,
  `0.91484375`, `0.98203125` und `0.98359375`.
- Die neuen Werte ergänzen die vorhandenen micro-/nanofeinen Opacity-Stufen und
  werden sowohl für `fill_opacity` als auch für `stroke_opacity` angeboten.
- Die Änderung ist deterministisch und katalogfrei; sie koppelt weder an
  `GE9012_6M` noch an eine andere Runtime-Bild-ID.

## 2) Perception-Lerneffekt

`GE9012_6M` bleibt ein beschreibungsbasierter Sonderfall für das
BackBottom-/hellgraues-Quadrat-Vokabular. Run VC erweitert nicht die reine
Bilddetektion, sondern den allgemeinen Opacity-Suchraum für vorhandene
`ColorPatch`-/`RectBorder`-Elemente, die aus neutral beschriebenen hellen
Rechteckflächen entstehen.

## 3) Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_color_patch_opacity_with_picofine_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rect_border_stroke_opacity_with_picofine_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_color_patch_opacity_with_nanofine_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rect_border_stroke_opacity_with_nanofine_probe` läuft grün mit `4 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün und bestätigt weiterhin `0` Runtime-ID-Vorkommen.
- `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ge9012-runVC --start GE9012_6M --end GE9012_6M --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; die isolierte GE9012_6M-Metrik bleibt stabil bei `Mean-Delta²=15386.639648` und `Fehler/Pixel=0.044122`.

## 4) Ergebnis / nächster Schritt

Run VC schließt den dokumentierten GE9012_6M-Feinschritt ab. Rechteck- und
Füllflächen können nun katalogfrei picofeine Opacity-Zwischenwerte bewerten; der
isolierte GE9012_6M-Einzellauf bleibt metrisch stabil. Das nächste Arbeitspaket
kann in der aktiven Plan-B-Rotation zu `GE9013_1M` wechseln oder weitere
allgemeine Bild-/Beschreibung-Fusion untersuchen.
