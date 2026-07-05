# Nächstes Arbeitspaket – GE1410_L Picofine-PolygonPath-Point-Probes Run VH (2026-07-05)

Run VH rotiert nach `docs/next_arbeitspaket_2026-07-05_runVG.md` auf den
aktiven Plan-B-Kandidaten `GE1410_L`. Der Fokus bleibt katalogfrei: allgemeine
`PolygonPath`-Punktkoordinaten erhalten zusätzlich picofeine Subpixel-Probes,
damit Diagramm-Dreiecke und vergleichbare Antialiasing-Kanten noch feinere
Rasterlagen bewerten können.

## 1) Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt für `PolygonPath.points[*][x/y]`
  zusätzlich zu den vorhandenen lokalen Punktvarianten nun picofeine
  `0.00015625`-Schritte in beide Richtungen.
- Die Erweiterung ist deterministisch und katalogfrei; sie koppelt weder an
  `GE1410_L` noch an eine andere Runtime-Bild-ID.
- Der neue Helper-Test erzwingt, dass ein picofeiner Punktversatz als beste
  Variante akzeptiert und im optimierten Geometry-IR zurückgegeben wird.

## 2) Perception-Lerneffekt

`GE1410_L` bleibt `generalisiert`: Achsen-/Linien- und Dreieck-Seeds entstehen
aus dem beschreibungs- und geometry-ir-basierten generischen Diagrammpfad.
Run VH erweitert nur den neutralen Optimierungsraum für vorhandene
`PolygonPath`-Dreiecke und führt keinen katalogspezifischen Sonderfall ein.

## 3) Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_points_with_picofine_subpixel_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_points_with_nanofine_subpixel_probe` läuft grün mit `2 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün und bestätigt weiterhin `0` Runtime-ID-Vorkommen.
- `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ge1410-runVH --start GE1410_L --end GE1410_L --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; die isolierte GE1410_L-Metrik bleibt stabil bei `Mean-Delta²=759.441589` und `Fehler/Pixel=0.010179`.

## 4) Ergebnis / nächster Schritt

Run VH schließt den dokumentierten GE1410_L-Feinschritt ab. `PolygonPath`-
Punktkoordinaten können nun katalogfrei picofeine Zwischenlagen bewerten; der
isolierte GE1410_L-Einzellauf bleibt metrisch stabil. Das nächste Arbeitspaket
kann in der aktiven Plan-B-Rotation zu `SE0041_1`, `GE9012_6M` oder `GE9013_1M`
wechseln oder weitere allgemeine Antialiasing-Probes untersuchen.
