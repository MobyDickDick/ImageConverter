# Nächstes Arbeitspaket – DLG0021 Subfine-Stroke-Gradient-Offset-Probes Run UK (2026-07-02)

Run UK rotiert nach dem GE9013_1M-Warm-Fill-Feinschritt wieder auf den aktiven
Plan-B-Kandidaten `DLG0021`. Der Fokus bleibt katalogfrei: `PolygonPath`-
Elemente mit Stroke-Gradient erhalten noch feinere Offset-Probes, damit der
beschriebene grüne Hakenverlauf ohne Bild-ID-Sonderfall enger in der
Elementoptimierung bewertet werden kann.

## 1) Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt für Prozent-Offsets in
  `stroke_gradient.stops` zusätzlich zu den vorhandenen ±10, ±5 und
  ±2,5 Prozentpunkten nun auch ±1,25 Prozentpunkte.
- Die Probes gelten für alle `PolygonPath`-Gradient-Stops mit Prozent-Offset und
  werden wie alle Elementprobes nur übernommen, wenn der gerenderte Fehler im
  Elementschritt strikt sinkt.
- Die Änderung ist deterministisch und katalogfrei; sie koppelt weder an
  `DLG0021` noch an eine andere Runtime-Bild-ID.

## 2) Perception-Lerneffekt

`DLG0021` bleibt `nur Sonderfall` auf Ebene des initialen Checkbox-/Haken-
Contracts. Run UK erweitert nicht die reine Bilddetektion, sondern den
allgemeinen Optimierungsraum für bereits vorhandene `PolygonPath`-Stroke-
Gradienten, wie sie aus neutralen Haken-/Konturbeschreibungen entstehen.

## 3) Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_stroke_gradient_offsets_with_subfine_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_stroke_gradient_offsets_with_fine_probe` läuft grün mit `2 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün und bestätigt weiterhin `0` Runtime-ID-Vorkommen.
- `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-dlg0021-runUK --start DLG0021 --end DLG0021 --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; die isolierte DLG0021-Metrik bleibt stabil bei `Mean-Delta²=17056.199219` und `Fehler/Pixel=0.077702`.

## 4) Ergebnis / nächster Schritt

Run UK schließt den dokumentierten DLG0021-Feinschritt ab. `PolygonPath`-
Stroke-Gradienten können nun katalogfrei noch feinere Offset-Varianten bewerten;
der isolierte DLG0021-Einzellauf bleibt stabil. Das nächste Arbeitspaket kann in
der aktiven Plan-B-Rotation zu `GE1410_L` wechseln oder weiteres allgemeines
PolygonPath-Antialiasing-Feintuning untersuchen.
