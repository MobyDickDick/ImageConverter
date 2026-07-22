# Nächstes Arbeitspaket – GE1410_L 2048th-Yoctofine-Polygon-Probes Run YZ (2026-07-22)

Run YZ arbeitet nach `docs/next_arbeitspaket_2026-07-22_runYY.md` den nächsten Schritt in der aktiven Plan-B-Rotation ab und wechselt zu `GE1410_L`. Der Fokus bleibt katalogfrei: Die allgemeinen `PolygonPath`-Punkt- und Stroke-Width-Probes erhalten eine 2048th-yoctofeine Zwischenstufe für antialiasingempfindliche Diagramm-/Dreiecksregistrierungen.

## Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt bei `PolygonPath.points[][]` zusätzlich `±0.0000000095367431640625` neben den bereits vorhandenen feinen Subpixel-Stufen.
- Die allgemeine Geometry-IR-Optimierung probt bei `PolygonPath.stroke_width` zusätzlich `±0.0000000095367431640625` neben den bereits vorhandenen feinen absoluten Stroke-Stufen.
- Neue Helper-Tests sichern, dass der reguläre Optimiererpfad die neue 2048th-yoctofeine Zwischenstufe nur bei sinkendem Fehler akzeptiert.
- Die Änderung hängt weder an `GE1410_L` noch an eine andere Runtime-Bild-ID.

## Plan-B-/Perception-Lerneffekt

`GE1410_L` bleibt ein beschreibungsbasierter Diagramm-/Dreieck-Contract. Run YZ erweitert nicht die reine Bilddetektion, sondern den allgemeinen Registrierungsraum für vorhandene `PolygonPath`-Dreiecke und -Konturen. Der Perception-Lerneffekt bleibt auf Seed-Ebene `generalisiert`; die nachgelagerte Polygon-Feinregistrierung ist ebenfalls katalogfrei generalisiert.

## Validierung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_points_with_2048th_yoctofine_subpixel_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_stroke_width_with_2048th_yoctofine_absolute_probe` läuft grün mit `2 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün mit `0 occurrences`.

## Ergebnis / nächster Schritt

Run YZ schließt den dokumentierten GE1410_L-Feinschritt auf Code- und Helper-Test-Ebene ab. PolygonPath-Diagramm- und Dreieckskonturen können nun eine zusätzliche 2048th-yoctofeine Punkt- und Stroke-Width-Zwischenregistrierung nutzen. Das nächste Arbeitspaket kann in der aktiven Plan-B-Rotation zu `SE0041_1` wechseln oder weiteres allgemeines Rule-/Square-Badge-Antialiasing-Feintuning prüfen.
