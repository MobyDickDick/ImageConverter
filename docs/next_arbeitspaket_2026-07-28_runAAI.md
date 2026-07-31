# Nächstes Arbeitspaket – GE1410_L 262144th-Yoctofine-Polygon-Probes Run AAI (2026-07-28)

Run AAI arbeitet nach `docs/next_arbeitspaket_2026-07-28_runAAH.md` den nächsten Schritt in der aktiven Plan-B-Rotation ab und wechselt zu `GE1410_L`. Der Fokus bleibt katalogfrei: Die allgemeinen `PolygonPath`-Punkt- und Stroke-Width-Probes erhalten eine 262144th-yoctofeine Zwischenstufe für antialiasingempfindliche Diagrammdreiecke und andere Polygonkonturen.

## Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt bei einzelnen `PolygonPath.points`-Koordinaten und bei `PolygonPath.stroke_width` zusätzlich `±0.00000000007450580596923828125`.
- Neue Helper-Tests sichern, dass der reguläre Optimiererpfad die neue 262144th-yoctofeine Zwischenstufe für Punktlage und Konturbreite nur bei sinkendem Fehler akzeptiert.
- Die Änderung hängt weder an `GE1410_L` noch an einer anderen Runtime-Bild-ID.

## Plan-B-/Perception-Lerneffekt

`GE1410_L` bleibt ein beschreibungsbasierter Diagrammdreieck-Contract. Run AAI erweitert nicht die reine Bilddetektion, sondern den allgemeinen Registrierungsraum für vorhandene Polygonpfade. Der Perception-Lerneffekt bleibt auf Seed-Ebene `nur Sonderfall`; die nachgelagerte Punkt- und Kontur-Feinregistrierung ist katalogfrei generalisiert.

## Validierung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_points_with_262144th_yoctofine_subpixel_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_stroke_width_with_262144th_yoctofine_absolute_probe` läuft grün mit `2 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün mit `0 occurrences`.

## Ergebnis / nächster Schritt

Run AAI schließt den dokumentierten GE1410_L-Feinschritt auf Code- und Helper-Test-Ebene ab. Polygonpfade können nun eine zusätzliche 262144th-yoctofeine Punkt- und Stroke-Width-Zwischenregistrierung nutzen. Das nächste Arbeitspaket kann in der aktiven Plan-B-Rotation zu `SE0041_1` wechseln oder weiteres allgemeines PolygonPath-Antialiasing-/Kontur-Feintuning prüfen.
