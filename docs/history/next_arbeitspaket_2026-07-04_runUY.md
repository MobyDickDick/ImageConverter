# Nächstes Arbeitspaket – GE9013_1M Nanofine-Warm-Fill-Probes Run UY (2026-07-04)

Run UY rotiert nach dem GE9012_6M-Opacity-Feinschritt auf den aktiven
Plan-B-Kandidaten `GE9013_1M`. Der Fokus bleibt katalogfrei: Die bestehenden
warmen `ColorPatch`-/`RectBorder`-Füllfarb-Probes erhalten zusätzliche
nanofeine Zwischenfarben für die rötlich-warme BackBottom-Quadratfamilie.

## 1) Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt für `ColorPatch` und
  `RectBorder` nun zusätzliche Zwischenfarben `#f2b8b5`, `#f2b9b6`,
  `#f2bab7` und `#f2bbb8` zwischen den bereits vorhandenen warmen
  BackBottom-Farbankern.
- Die neuen Probes gelten neutral für flächen- und rechteckbasierte IR-Elemente
  und werden wie alle Elementprobes nur übernommen, wenn der gerenderte Fehler
  im Elementschritt strikt sinkt.
- Die Änderung ist deterministisch und katalogfrei; sie koppelt weder an
  `GE9013_1M` noch an eine andere Runtime-Bild-ID.

## 2) Perception-Lerneffekt

`GE9013_1M` bleibt ein beschreibungsbasierter Sonderfall für das
BackBottom-/hellgraues-Quadrat-Vokabular. Run UY erweitert nicht die reine
Bilddetektion, sondern den allgemeinen Optimierungsraum für vorhandene
`ColorPatch`-/`RectBorder`-Füllfarben, wie sie aus neutral beschriebenen hellen
Rechteckflächen entstehen.

## 3) Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rect_to_nanofine_warm_light_fill tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rect_to_subfine_warm_light_fill tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rect_to_fine_warm_light_fill` läuft grün mit `3 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün und bestätigt weiterhin `0` Runtime-ID-Vorkommen.
- `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ge9013-runUY --start GE9013_1M --end GE9013_1M --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; die isolierte GE9013_1M-Metrik bleibt stabil bei `Mean-Delta²=12989.524414` und `Fehler/Pixel=0.035766`.

## 4) Ergebnis / nächster Schritt

Run UY schließt den dokumentierten GE9013_1M-Feinschritt ab. Rechteck- und
Füllflächen können nun katalogfrei nanofeine warme Füllfarbvarianten bewerten;
der isolierte GE9013_1M-Einzellauf bleibt metrisch stabil. Das nächste
Arbeitspaket kann in der aktiven Plan-B-Rotation zu `DLG0021` wechseln oder
weitere allgemeine Bild-/Beschreibung-Fusion untersuchen.
