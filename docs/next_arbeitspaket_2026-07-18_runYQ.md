# Nächstes Arbeitspaket – GE1410_L 1024th-Yoctofine-PolygonPath-Probes Run YQ (2026-07-18)

Run YQ arbeitet nach `docs/next_arbeitspaket_2026-07-17_runYP.md` den nächsten kleinen Feinschritt in der aktiven Plan-B-Rotation ab und bleibt bei `GE1410_L`. Der Fokus bleibt katalogfrei: Die allgemeinen `PolygonPath`-Punkt- und Stroke-Width-Probes erhalten eine weitere ultrafeine Zwischenstufe für antialiasing-empfindliche Diagramm-/Dreieckskonturen.

## Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt bei `PolygonPath.points[*][x|y]` zusätzlich `±0.000000019073486328125` als normalisierte 1024th-yoctofeine Subpixel-Zwischenstufe.
- Die allgemeine Geometry-IR-Optimierung probt bei `PolygonPath.stroke_width` zusätzlich `±0.000000019073486328125` als absolute 1024th-yoctofeine Stroke-Width-Zwischenstufe.
- Neue Helper-Tests sichern ab, dass beide Zwischenstufen über den regulären Optimiererpfad akzeptiert werden, wenn sie den Fehler senken.
- Die Änderung hängt weder an `GE1410_L` noch an eine andere Runtime-Bild-ID.

## Plan-B-/Perception-Lerneffekt

`GE1410_L` bleibt ein beschreibungsbasierter Diagramm-/Dreieck-Contract aus `PolygonPath`-Primitiven. Run YQ erweitert nicht die reine Bilddetektion, sondern den allgemeinen Registrierungsraum vorhandener Polygonpunkte und Konturbreiten. Der Perception-Lerneffekt bleibt damit `nur Sonderfall` für den ursprünglichen Contract, aber `generalisiert` für den nachgelagerten Optimiererpfad.

## Validierung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_points_with_1024th_yoctofine_subpixel_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_stroke_width_with_1024th_yoctofine_absolute_probe` läuft grün mit `2 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün mit `0 occurrences`.

## Ergebnis / nächster Schritt

Run YQ schließt den dokumentierten GE1410_L-Feinschritt auf Code- und Testebene ab. PolygonPath-Punkte und -Konturbreiten können nun eine zusätzliche 1024th-yoctofeine Zwischenregistrierung nutzen. Das nächste Arbeitspaket kann in der aktiven Plan-B-Rotation zu `SE0041_1` wechseln oder weiteres allgemeines Diagramm-/Polygon-Feintuning prüfen.
