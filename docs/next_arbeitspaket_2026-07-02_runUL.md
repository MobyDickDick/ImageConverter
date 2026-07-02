# Nächstes Arbeitspaket – GE1410_L Subfine-PolygonPath-Punktprobes Run UL (2026-07-02)

Run UL rotiert nach dem DLG0021-Gradient-Feinschritt auf den aktiven
Plan-B-Kandidaten `GE1410_L`. Der Fokus bleibt katalogfrei: `PolygonPath`-
Elemente erhalten noch feinere lokale Punktprobes, damit antialiasing-sensitive
Dreiecks- und Hakenkonturen ohne Bild-ID-Sonderfall enger in der allgemeinen
Elementoptimierung bewertet werden können.

## 1) Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt für `PolygonPath.points`
  zusätzlich zu den vorhandenen ±2, ±1 und ±0,5 Prozentpunkten nun auch
  ±0,25 Prozentpunkte je Koordinate.
- Die Probes gelten für alle `PolygonPath`-Elemente und werden wie alle
  Elementprobes nur übernommen, wenn der gerenderte Fehler im Elementschritt
  strikt sinkt.
- Die Änderung ist deterministisch und katalogfrei; sie koppelt weder an
  `GE1410_L` noch an eine andere Runtime-Bild-ID.

## 2) Perception-Lerneffekt

`GE1410_L` bleibt auf Ebene der Achsen-/Linien- und Dreieck-Seeds
`generalisiert`. Run UL erweitert nicht die reine Bilddetektion, sondern den
allgemeinen Optimierungsraum für bereits vorhandene `PolygonPath`-Konturen, wie
sie aus neutralen Diagramm- und Dreieckbeschreibungen entstehen.

## 3) Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_points_with_subfine_subpixel_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_points_with_subpixel_probe` läuft grün mit `2 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün und bestätigt weiterhin `0` Runtime-ID-Vorkommen.
- `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ge1410-runUL --start GE1410_L --end GE1410_L --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; die isolierte GE1410_L-Metrik bleibt im kompakten semantischen Diagrammpfad stabil bei `Mean-Delta²=763.174377` und `Fehler/Pixel=0.010206`.

## 4) Ergebnis / nächster Schritt

Run UL schließt den dokumentierten GE1410_L-Feinschritt ab. `PolygonPath`-
Konturen können nun katalogfrei noch feinere Punktvarianten bewerten; der
isolierte GE1410_L-Einzellauf bleibt stabil. Das nächste Arbeitspaket kann in
der aktiven Plan-B-Rotation zu `SE0041_1` wechseln oder weiteres allgemeines
PolygonPath-Antialiasing-/Stroke-Feintuning untersuchen.
