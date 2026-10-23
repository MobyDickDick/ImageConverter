# Nächstes Arbeitspaket – GE1410_L Zeptofine-PolygonPath-Probes Run VS (2026-07-07)

Run VS rotiert nach dem DLG0021-Attofine-Gradient-Offset-Schritt aus Run VR
zurück zum aktiven Plan-B-Kandidaten `GE1410_L`. Der Fokus bleibt katalogfrei:
Die allgemeinen `PolygonPath`-Punkt- und `stroke_width`-Probes werden um eine
zeptofeine Zwischenstufe erweitert, damit Diagramm-Dreiecke und vergleichbare
Antialiasing-Kanten noch kleinere Punkt- und Konturbreitenverschiebungen
bewerten können.

## 1) Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt für `PolygonPath.points`
  zusätzlich zeptofeine Koordinaten-Deltas von `±0.00001953125` in
  normalisierten Canvas-Koordinaten.
- Die allgemeine Geometry-IR-Optimierung probt für `PolygonPath.stroke_width`
  zusätzlich zeptofeine absolute Deltas von `±0.00001953125`.
- Die neue Zwischenstufe ergänzt die vorhandenen attofeinen `±0.0000390625`-
  Probes und wird wie alle Elementprobes nur übernommen, wenn der gerenderte
  Fehler im Elementschritt strikt sinkt.
- Die Änderung ist deterministisch und katalogfrei; sie koppelt weder an
  `GE1410_L` noch an eine andere Runtime-Bild-ID.

## 2) Perception-Lerneffekt

`GE1410_L` bleibt für Achsen-/Linien- und Dreieck-Seeds `generalisiert`. Run VS
erweitert nicht die initiale Bilddetektion, sondern den allgemeinen
Optimierungsraum für bereits erkannte oder beschreibungsbasiert erzeugte
`PolygonPath`-Geometrien.

## 3) Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_points_with_zeptofine_subpixel_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_stroke_width_with_zeptofine_absolute_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_points_with_attofine_subpixel_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_stroke_width_with_attofine_absolute_probe` läuft grün mit `4 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün und bestätigt weiterhin `0` Runtime-ID-Vorkommen.
- `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ge1410-runVS --start GE1410_L --end GE1410_L --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; der isolierte GE1410_L-Einzellauf bleibt stabil bei `Mean-Delta²=759.441589` und `Fehler/Pixel=0.010179`.

## 4) Ergebnis / nächster Schritt

Run VS schließt den dokumentierten GE1410_L-Feinschritt ab. `PolygonPath`-
Dreiecke und -Konturen können nun katalogfrei zeptofeine Punkt- und
Stroke-Width-Varianten bewerten; der isolierte GE1410_L-Einzellauf bleibt
stabil. Das nächste Arbeitspaket kann in der aktiven Plan-B-Rotation zu
`SE0041_1` wechseln oder weiteres allgemeines Antialiasing-Feintuning prüfen.
