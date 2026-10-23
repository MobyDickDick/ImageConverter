# Nächstes Arbeitspaket – GE9013_1M Femtofine-Warmfill-Probes Run VV (2026-07-08)

Run VV rotiert nach dem GE9012_6M-Attofine-Opacity-Schritt aus Run VU auf den aktiven Plan-B-Kandidaten `GE9013_1M`. Der Fokus bleibt katalogfrei: Die allgemeine `ColorPatch`-/`RectBorder`-Füllfarbregistrierung bekommt zusätzliche femtofeine warme Zwischenfarben, damit BackBottom-/hellgraue Rechteckflächen noch kleinere Rotkanal- und Warmton-Abstufungen bewerten können.

## 1) Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt für `ColorPatch`- und `RectBorder`-Elemente zusätzlich die warmen Zwischenfarben `#f3b9b5` und `#f3b9b6`.
- Die neuen Werte ergänzen die vorhandenen warmen `#f2b9b5`-, `#f2b9b6`- und `#f2b9b7`-Probes und werden wie alle Elementprobes nur übernommen, wenn der gerenderte Fehler im Elementschritt strikt sinkt.
- Die Änderung ist deterministisch und katalogfrei; sie koppelt weder an `GE9013_1M` noch an eine andere Runtime-Bild-ID.

## 2) Perception-Lerneffekt

`GE9013_1M` bleibt auf Ebene des BackBottom-/hellgraues-Quadrat-Vokabulars ein `nur Sonderfall`-Signal. Run VV erweitert nicht die Bilddetektion, sondern den allgemeinen Optimierungsraum für bereits vorhandene rechteckige Füllflächen, die aus neutralen Beschreibungs- oder Perception-Seeds entstehen.

## 3) Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rect_to_femtofine_warm_light_fill tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rect_to_picofine_warm_light_fill tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rect_to_nanofine_warm_light_fill` läuft grün mit `3 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün und bestätigt weiterhin `0` Runtime-ID-Vorkommen.
- `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ge9013-runVV --start GE9013_1M --end GE9013_1M --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; der isolierte GE9013_1M-Einzellauf bleibt stabil bei `Mean-Delta²=12989.524414` und `Fehler/Pixel=0.035766`.

## 4) Ergebnis / nächster Schritt

Run VV schließt den dokumentierten GE9013_1M-Feinschritt ab. Rechteckige Füllelemente können nun katalogfrei femtofeine warme Farbvarianten bewerten; der isolierte GE9013_1M-Einzellauf bleibt metrisch stabil. Das nächste Arbeitspaket kann in der aktiven Plan-B-Rotation zu `DLG0021` wechseln oder weiteres allgemeines Antialiasing-Feintuning prüfen.
