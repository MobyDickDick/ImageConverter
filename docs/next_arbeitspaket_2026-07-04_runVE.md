# Nächstes Arbeitspaket – PolygonPath Nanofine-Stroke-Width-Probes Run VE (2026-07-04)

Run VE setzt nach `docs/next_arbeitspaket_2026-07-04_runVD.md` den dort
dokumentierten Anschluss „weitere allgemeine Antialiasing-/Gradient-
Feintuning-Probes“ als kleinen katalogfreien Stroke-Schritt fort. Der Fokus
bleibt auf vorhandenen `PolygonPath`-Konturen: Nach den microfeinen absoluten
`stroke_width`-Probes erhalten sie zusätzlich nanofeine Zwischenbreiten, damit
Diagramm-, Dreieck- und Hakenkonturen noch enger gegen Antialiasing-Rasterlagen
bewertet werden können.

## 1) Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt für `PolygonPath`-Elemente mit
  `stroke_width` zusätzlich zu den vorhandenen absoluten Konturstärken-Varianten
  nun nanofeine `±0.0003125`-Schritte.
- Die neuen Probes werden wie alle Elementprobes nur übernommen, wenn der
  gerenderte Fehler im Elementschritt strikt sinkt.
- Die Änderung ist deterministisch und katalogfrei; sie koppelt weder an
  `GE1410_L` noch an eine andere Runtime-Bild-ID.
- Ein Detailtest sichert die neue Kandidatenstufe explizit gegen Regression ab.

## 2) Perception-Lerneffekt

Der Schritt erweitert nicht die reine Bilddetektion, sondern den allgemeinen
Optimierungsraum für vorhandene `PolygonPath`-Konturstärken. Damit profitieren
alle neutral abgeleiteten Polygonpfade, ohne eine bildspezifische Sonderregel
einzuführen. Der Lerneffekt bleibt für `GE1410_L` daher `generalisiert`, weil
der semantische Diagramm-/Dreieck-Pfad bereits katalogfrei abgeleitet wird und
nur sein allgemeiner Stroke-Suchraum verfeinert wurde.

## 3) Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_stroke_width_with_absolute_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_stroke_width_with_fine_absolute_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_stroke_width_with_subfine_absolute_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_stroke_width_with_ultrafine_absolute_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_stroke_width_with_microfine_absolute_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_stroke_width_with_nanofine_absolute_probe` läuft grün mit `6 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün und bestätigt weiterhin `0` Runtime-ID-Vorkommen.
- `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ge1410-runVE --start GE1410_L --end GE1410_L --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; die isolierte GE1410_L-Metrik bleibt stabil bei `Mean-Delta²=759.441589` und `Fehler/Pixel=0.010179`.

## 4) Ergebnis / nächster Schritt

Run VE schließt den generischen PolygonPath-Stroke-Feinschritt ab. PolygonPath-
Konturstärken können nun katalogfrei nanofeine Zwischenbreiten bewerten. Das
nächste Arbeitspaket kann wieder in der aktiven Plan-B-Rotation fortfahren oder
weitere allgemeine Antialiasing-/Gradient-Feintuning-Probes untersuchen.
