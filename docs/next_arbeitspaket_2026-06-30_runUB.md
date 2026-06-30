# Nächstes Arbeitspaket – GE1410_L feine PolygonPath-Punktprobes Run UB (2026-06-30)

Run UB rotiert nach dem DLG0021-Offset-Recheck aus Run UA wieder auf den
zweitpriorisierten aktiven Plan-B-Kandidaten `GE1410_L` aus
`PLAN_B_KANDIDATEN.md`. Fokus ist weiterhin kein Bild-ID-Sonderfall, sondern
eine katalogfreie Verfeinerung der allgemeinen Geometry-IR-Elementoptimierung:
`PolygonPath`-Punkte erhalten zusätzlich feine ±0.005-Koordinatenprobes für
antialiasing-sensitive Dreiecks- und Konturprimitive.

## 1) Umsetzung

- Die bestehende allgemeine Geometry-IR-Optimierung testet für
  `PolygonPath.points[*][x|y]` zusätzlich zu ±0.01/±0.02 nun auch die neutralen
  Subpixel-Probes ±0.005.
- Die Erweiterung bleibt elementweise, deterministisch und katalogfrei; sie
  greift für alle `PolygonPath`-Primitive und koppelt nicht an `GE1410_L` oder
  andere Runtime-Bild-IDs.
- Ein gezielter Helper-Test sichert ab, dass ein strikt verbessernder
  ±0.005-Punktkandidat akzeptiert wird.

## 2) Perception-Lerneffekt

`GE1410_L` bleibt `generalisiert`: Achsen-/Linien- und Dreieck-Seeds entstehen
weiterhin aus der Beschreibung und werden als neutrale `PolygonPath`-Primitive
optimiert. Run UB erweitert nicht die Perception-Erkennung selbst, sondern den
katalogfreien Optimierungsraum für bereits erkannte Polygonpfade.

## 3) Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_points_with_subpixel_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_points_locally` läuft grün mit `2 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün und bestätigt weiterhin `0` Runtime-ID-Vorkommen.
- `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ge1410-runUB --start GE1410_L --end GE1410_L --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; die isolierte GE1410_L-Metrik sinkt von zuletzt `Mean-Delta²=777.012817` auf `759.473572` bei `Fehler/Pixel=0.010097`.

## 4) Ergebnis / nächster Schritt

Run UB schließt den dokumentierten GE1410_L-Feinschritt ab. Die neuen feinen
`PolygonPath`-Punktprobes sind abgesichert und verbessern den isolierten
GE1410_L-Einzellauf leicht. Das nächste Arbeitspaket kann in der aktiven
Plan-B-Rotation zu `SE0041_1` wechseln oder weitere katalogfreie
PolygonPath-/Antialiasing-Probes untersuchen.
