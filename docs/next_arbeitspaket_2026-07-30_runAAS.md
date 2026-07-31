# Nächstes Arbeitspaket – GE1410_L 1048576th-Yoctofine-Polygon-Probes Run AAS (2026-07-30)

Run AAS arbeitet nach `docs/next_arbeitspaket_2026-07-29_runAAR.md` den nächsten Schritt in der aktiven Plan-B-Rotation ab und wechselt zu `GE1410_L`. Der Fokus bleibt katalogfrei: Die allgemeinen `PolygonPath`-Punkt- und Stroke-Width-Probes erhalten eine 1048576th-yoctofeine Zwischenstufe für antialiasingempfindliche Diagrammdreiecke und andere Polygonkonturen.

## Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt bei einzelnen `PolygonPath.points`-Koordinaten und bei `PolygonPath.stroke_width` zusätzlich `±0.0000000000186264514923095703125`.
- Neue Helper-Tests sichern, dass der reguläre Optimiererpfad die neue 1048576th-yoctofeine Zwischenstufe für Punktlage und Konturbreite nur bei sinkendem Fehler akzeptiert.
- Die Änderung hängt weder an `GE1410_L` noch an einer anderen Runtime-Bild-ID.

## Plan-B-/Perception-Lerneffekt

`GE1410_L` bleibt ein beschreibungsbasierter Diagrammdreieck-Contract. Run AAS erweitert nicht die reine Bilddetektion, sondern den allgemeinen Registrierungsraum für vorhandene Polygonpfade. Der Perception-Lerneffekt bleibt auf Seed-Ebene `nur Sonderfall`; die nachgelagerte Punkt- und Kontur-Feinregistrierung ist katalogfrei generalisiert.

## Validierung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_points_with_1048576th_yoctofine_subpixel_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_stroke_width_with_1048576th_yoctofine_absolute_probe` läuft grün mit `2 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün mit `0 occurrences`.

## Ergebnis / nächster Schritt

Run AAS schließt den dokumentierten GE1410_L-Feinschritt auf Code- und Helper-Test-Ebene ab. Polygonpfade können nun eine zusätzliche 1048576th-yoctofeine Punkt- und Stroke-Width-Zwischenregistrierung nutzen. Das nächste Arbeitspaket kann in der aktiven Plan-B-Rotation zu `SE0041_1` wechseln oder weiteres allgemeines PolygonPath-Antialiasing-/Kontur-Feintuning prüfen.
