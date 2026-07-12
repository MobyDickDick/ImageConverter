# Nächstes Arbeitspaket – GE1410_L Sixteenth-Yoctofine-PolygonPath-Probes Run XO (2026-07-12)

Run XO rotiert nach `docs/next_arbeitspaket_2026-07-12_runXN.md` in der aktiven Plan-B-Kandidatenliste zu `GE1410_L`. Der Fokus bleibt katalogfrei: Die allgemeinen `PolygonPath`-Punkt- und Stroke-Width-Probes erhalten eine sixteenth-yoctofeine Zwischenstufe für antialiasing-empfindliche Diagramm-Dreiecke.

## Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt bei `PolygonPath.stroke_width` zusätzlich `±0.000001220703125` als absolute Delta-Stufe.
- Die allgemeine Geometry-IR-Optimierung probt bei einzelnen `PolygonPath.points` zusätzlich `±0.000001220703125` als Subpixel-Delta-Stufe.
- Zwei neue Helper-Tests sichern die neuen Punkt- und Stroke-Width-Probes separat ab.
- Die Änderung hängt weder an `GE1410_L` noch an eine andere Runtime-Bild-ID.

## Plan-B-/Perception-Lerneffekt

`GE1410_L` bleibt ein katalogfrei generalisierter Diagramm-/Dreieck-Contract: Achsen, Linien und Dreiecke entstehen aus neutralen Beschreibungssignalen und werden anschließend über allgemeine `PolygonPath`-Optimierung feinregistriert. Run XO erweitert nicht die reine Bilddetektion, sondern den allgemeinen Registrierungsraum für vorhandene Polygonpfade. Der Perception-Lerneffekt bleibt für `GE1410_L` daher `generalisiert`.

## Validierung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_points_with_sixteenth_yoctofine_subpixel_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_stroke_width_with_sixteenth_yoctofine_absolute_probe` läuft grün mit `2 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün mit `0 occurrences`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. ICC_MAX_QUALITY_PASSES=1 timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ge1410-runXO --start GE1410_L --end GE1410_L --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; der beste isolierte GE1410_L-Pass meldet `Mean-Delta²=618.534424` und `Fehler/Pixel=0.011102`.

## Ergebnis

Run XO schließt den dokumentierten GE1410_L-Feinschritt auf Code-, Test- und isolierter Recheck-Ebene ab. Polygonpfad-Punkte und -Konturstärken können nun eine sixteenth-yoctofeine Zwischenregistrierung nutzen; der isolierte GE1410_L-Einzellauf bleibt grün. Das nächste Arbeitspaket kann in der aktiven Plan-B-Rotation zu `SE0041_1` wechseln oder weiteres allgemeines PolygonPath-/Diagramm-Antialiasing-Feintuning prüfen.
