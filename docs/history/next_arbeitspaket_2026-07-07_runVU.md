# Nächstes Arbeitspaket – GE9012_6M Attofine-Opacity-Probes Run VU (2026-07-07)

Run VU rotiert nach dem SE0041_1-Zeptofine-Rule-Stroke-Schritt aus Run VT
zurück zum aktiven Plan-B-Kandidaten `GE9012_6M`. Der Fokus bleibt katalogfrei:
Die allgemeinen `ColorPatch`-/`RectBorder`-Opacity-Probes werden um attofeine
Zwischenwerte ergänzt, damit BackBottom-/hellgraue Rechteckflächen und Konturen
noch kleinere Alpha-Kantenverschiebungen bewerten können.

## 1) Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt für `ColorPatch`- und
  `RectBorder`-Elemente zusätzlich attofeine Opacity-Zwischenwerte
  `0.9826171875` und `0.9830078125`.
- Die neue Zwischenstufe ergänzt die vorhandenen femtofeinen Werte um
  `0.9828125` und wird wie alle Elementprobes nur übernommen, wenn der
  gerenderte Fehler im Elementschritt strikt sinkt.
- Die Änderung ist deterministisch und katalogfrei; sie koppelt weder an
  `GE9012_6M` noch an eine andere Runtime-Bild-ID.

## 2) Perception-Lerneffekt

`GE9012_6M` bleibt auf Ebene des BackBottom-/hellgraues-Quadrat-Vokabulars ein
`nur Sonderfall`-Signal. Run VU erweitert nicht die Bilddetektion, sondern den
allgemeinen Optimierungsraum für bereits vorhandene rechteckige Flächen und
Konturen, die aus neutralen Beschreibungs- oder Perception-Seeds entstehen.

## 3) Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_color_patch_opacity_with_attofine_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rect_border_stroke_opacity_with_attofine_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_color_patch_opacity_with_femtofine_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rect_border_stroke_opacity_with_femtofine_probe` läuft grün mit `4 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün und bestätigt weiterhin `0` Runtime-ID-Vorkommen.
- `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ge9012-runVU --start GE9012_6M --end GE9012_6M --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; der isolierte GE9012_6M-Einzellauf bleibt stabil bei `Mean-Delta²=15386.639648` und `Fehler/Pixel=0.044122`.

## 4) Ergebnis / nächster Schritt

Run VU schließt den dokumentierten GE9012_6M-Feinschritt ab. Rechteckige Füll-
und Konturelemente können nun katalogfrei attofeine Opacity-Varianten bewerten;
der isolierte GE9012_6M-Einzellauf bleibt stabil. Das nächste Arbeitspaket kann
in der aktiven Plan-B-Rotation zu `GE9013_1M` wechseln oder weiteres allgemeines
Antialiasing-Feintuning prüfen.
