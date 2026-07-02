# Nächstes Arbeitspaket – GE9013_1M feine Warm-Fill-Probes Run UJ (2026-07-02)

Run UJ rotiert nach dem GE9012_6M-Opacity-Feinschritt aus Run UI auf den
aktiven Plan-B-Kandidaten `GE9013_1M` aus `PLAN_B_KANDIDATEN.md`. Der Fokus
bleibt katalogfrei: rechteckige `ColorPatch`-/`RectBorder`-Füllflächen erhalten
zusätzliche feine warme Zwischenfarb-Probes, damit helle BackBottom-/Quadrat-
Flächen mit warmem Antialiasing ohne Bild-ID-Sonderfall enger bewertet werden
können.

## 1) Umsetzung

- Die allgemeine Geometry-IR-Optimierung erweitert die neutrale Rechteck-
  Füllfarbpalette um feine warme Zwischenstufen zwischen den bereits vorhandenen
  hellroten Probeankern.
- Die Kandidaten bleiben elementweise, deterministisch und katalogfrei; sie
  werden wie alle Elementprobes nur übernommen, wenn der gerenderte Fehler im
  Elementschritt strikt sinkt.
- Die Änderung koppelt weder an `GE9013_1M` noch an eine andere Runtime-Bild-ID.

## 2) Perception-Lerneffekt

`GE9013_1M` bleibt `nur Sonderfall` auf Ebene des initialen BackBottom-/hellgraues-
Quadrat-Contracts. Run UJ erweitert nicht die Bilddetektion, sondern den
allgemeinen Optimierungsraum für bereits vorhandene Rechteck-Füllprimitive, wie
sie aus neutralen Rechteck- und Füllflächenbeschreibungen entstehen.

## 3) Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rect_to_fine_warm_light_fill tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_neutral_rect_to_warm_light_fill` läuft grün mit `2 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün und bestätigt weiterhin `0` Runtime-ID-Vorkommen.
- `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ge9013-runUJ --start GE9013_1M --end GE9013_1M --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; die isolierte GE9013_1M-Metrik bleibt stabil bei `Mean-Delta²=12989.524414` und `Fehler/Pixel=0.035766`.

## 4) Ergebnis / nächster Schritt

Run UJ schließt den dokumentierten GE9013_1M-Feinschritt ab. Rechteckige
Füllflächen können nun katalogfrei feinere warme Zwischenfarben bewerten; der
isolierte GE9013_1M-Einzellauf bleibt stabil. Das nächste Arbeitspaket kann in
der aktiven Plan-B-Rotation wieder zu `DLG0021` wechseln oder weiteres
allgemeines Rect-/ColorPatch-Antialiasing-Feintuning untersuchen.
