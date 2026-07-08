# Nächstes Arbeitspaket – GE9013_1M Femtofine-Warm-Fill-Probes Run VV (2026-07-08)

Run VV rotiert nach dem GE9012_6M-Attofine-Opacity-Schritt aus Run VU zum
aktiven Plan-B-Kandidaten `GE9013_1M`. Der Fokus bleibt katalogfrei: Die
allgemeine `ColorPatch`-/`RectBorder`-Füllfarbpalette erhält eine weitere warme
Zwischenfarbe, damit bereits erkannte BackBottom-/hellgraue Rechteckflächen eine
minimal feinere Rot-/Orange-Kante bewerten können.

## 1) Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt für `ColorPatch`- und
  `RectBorder`-Elemente zusätzlich die femtofeine warme Zwischenfarbe
  `#f2bab8`.
- Die neue Farbe ergänzt die vorhandene warme Palette zwischen den bereits
  probierten `#f2bab7`- und helleren Nachbarwerten und wird wie alle
  Elementprobes nur übernommen, wenn der gerenderte Fehler im Elementschritt
  strikt sinkt.
- Die Änderung ist deterministisch und katalogfrei; sie koppelt weder an
  `GE9013_1M` noch an eine andere Runtime-Bild-ID.

## 2) Perception-Lerneffekt

`GE9013_1M` bleibt auf Ebene des BackBottom-/hellgraues-Quadrat-Vokabulars ein
`nur Sonderfall`-Signal. Run VV erweitert nicht die Bilddetektion, sondern den
allgemeinen Optimierungsraum für bereits vorhandene rechteckige Flächen und
Konturen, die aus neutralen Beschreibungs- oder Perception-Seeds entstehen.

## 3) Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rect_to_femtofine_warm_light_fill tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rect_to_picofine_warm_light_fill` läuft grün mit `2 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün und bestätigt weiterhin `0` Runtime-ID-Vorkommen.
- `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ge9013-runVV --start GE9013_1M --end GE9013_1M --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; der isolierte GE9013_1M-Einzellauf bleibt stabil bei `Mean-Delta²=12989.524414` und `Fehler/Pixel=0.035766`.

## 4) Ergebnis / nächster Schritt

Run VV schließt den dokumentierten GE9013_1M-Feinschritt ab. Rechteckige Füll-
und Konturelemente können nun katalogfrei eine weitere femtofeine warme
Füllfarbe bewerten; der isolierte GE9013_1M-Einzellauf bleibt stabil. Das
nächste Arbeitspaket kann in der aktiven Plan-B-Rotation wieder zu `DLG0021`
wechseln oder weiteres allgemeines Antialiasing-Feintuning prüfen.
