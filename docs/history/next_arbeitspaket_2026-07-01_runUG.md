# Nächstes Arbeitspaket – GE1410_L feine PolygonPath-Stroke-Width-Probes Run UG (2026-07-01)

Run UG rotiert nach dem DLG0021-Gradient-Offset-Schritt aus Run UF zurück auf
`GE1410_L` aus der aktiven Plan-B-Liste. Der Fokus bleibt katalogfrei: Für
antialiasing-sensitive Diagramm- und Dreieckskonturen ergänzt der Geometry-IR-
Optimierer feinere absolute `PolygonPath.stroke_width`-Probes.

## 1) Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt für `PolygonPath`-Elemente mit
  `stroke_width` zusätzlich zu den vorhandenen relativen und absoluten ±0,01-
  Varianten nun auch feine absolute ±0,005-Schritte.
- Die neuen Probes werden wie alle Elementkandidaten nur übernommen, wenn der
  gerenderte Fehler im aktuellen Elementschritt strikt sinkt.
- Die Änderung ist deterministisch und katalogfrei; sie koppelt weder an
  `GE1410_L` noch an eine andere Runtime-Bild-ID.

## 2) Perception-Lerneffekt

`GE1410_L` bleibt `generalisiert`: Achsen-/Linien- und Dreieck-Seeds entstehen
weiterhin aus beschreibungsbasierten, neutralen `PolygonPath`-Primitiven. Run UG
erweitert nicht die initiale Bilddetektion, sondern den allgemeinen
Optimierungsraum für vorhandene Polygonkonturen mit kleinen Antialiasing-
Abweichungen.

## 3) Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_stroke_width_with_absolute_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_stroke_width_with_fine_absolute_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_points_with_subpixel_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_points_locally` läuft grün mit `4 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün und bestätigt weiterhin `0` Runtime-ID-Vorkommen.
- `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ge1410-runUG --start GE1410_L --end GE1410_L --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; die isolierte GE1410_L-Metrik liegt bei `Mean-Delta²=763.174377` und `Fehler/Pixel=0.010206`.

## 4) Ergebnis / nächster Schritt

Run UG schließt den dokumentierten GE1410_L-Feinschritt ab. `PolygonPath`-
Konturen können nun katalogfrei feinere absolute Stroke-Width-Varianten
bewerten; der isolierte GE1410_L-Einzellauf bleibt im kompakten semantischen
Diagrammpfad. Das nächste Arbeitspaket kann in der aktiven Plan-B-Rotation zu
`SE0041_1` wechseln oder weiteres allgemeines PolygonPath-/Antialiasing-
Feintuning untersuchen.
