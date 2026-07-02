# Nächstes Arbeitspaket – GE9013_1M Subfine-Warm-Fill-Probes Run UO (2026-07-02)

Run UO rotiert nach dem GE9012_6M-Opacity-Feinschritt auf den aktiven
Plan-B-Kandidaten `GE9013_1M`. Der Fokus bleibt katalogfrei: die bereits
vorhandene warme BackBottom-/hellgraues-Quadrat-Füllfarbpalette wird um
feinere Zwischenfarben ergänzt, damit leichte rötliche Antialiasing- und
Flächenfarbabweichungen im allgemeinen Elementoptimierer bewertet werden
können.

## 1) Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt für `ColorPatch`- und
  `RectBorder`-Füllungen zusätzlich die warmen Zwischenfarben `#f2b9b5`,
  `#f2bbb7`, `#f3bdb9`, `#f3bfba`, `#f4c1bd` und `#f4c3bf`.
- Die neuen Probes ergänzen die vorhandenen warmen hellen Füllfarbstufen und
  werden wie alle Elementprobes nur übernommen, wenn der gerenderte Fehler im
  Elementschritt strikt sinkt.
- Die Änderung ist deterministisch und katalogfrei; sie koppelt weder an
  `GE9013_1M` noch an eine andere Runtime-Bild-ID.

## 2) Perception-Lerneffekt

`GE9013_1M` bleibt ein beschreibungsbasierter BackBottom-/hellgraues-Quadrat-
Sonderfall. Run UO erweitert nicht die reine Bilddetektion, sondern den
allgemeinen Optimierungsraum für bereits vorhandene rechteckige Flächen- und
Rahmenelemente mit warmer heller Füllung.

## 3) Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rect_to_subfine_warm_light_fill tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rect_to_fine_warm_light_fill` läuft grün mit `2 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün und bestätigt weiterhin `0` Runtime-ID-Vorkommen.
- `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ge9013-runUO --start GE9013_1M --end GE9013_1M --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; die isolierte GE9013_1M-Metrik bleibt stabil bei `Mean-Delta²=12989.524414` und `Fehler/Pixel=0.035766`.

## 4) Ergebnis / nächster Schritt

Run UO schließt den dokumentierten GE9013_1M-Feinschritt ab. Rechteckige
Geometry-IR-Flächen und -Rahmen können nun katalogfrei feinere warme
Füllfarb-Zwischenstufen bewerten; der isolierte GE9013_1M-Einzellauf bleibt
stabil. Das nächste Arbeitspaket kann in der aktiven Plan-B-Rotation zu
`DLG0021` wechseln oder weiteres allgemeines Rect-/BackBottom-Feintuning
untersuchen.
