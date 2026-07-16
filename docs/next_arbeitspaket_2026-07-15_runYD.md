# Nächstes Arbeitspaket – GE1410_L 64th-/128th-Yoctofine-PolygonPath-Probes Run YD (2026-07-15)

Run YD arbeitet nach `docs/next_arbeitspaket_2026-07-15_runYC.md` den nächsten Schritt in der aktiven Plan-B-Rotation ab und wechselt zu `GE1410_L`. Der Fokus bleibt katalogfrei: Die allgemeinen `PolygonPath`-Punkt- und Stroke-Width-Probes erhalten eine weitere ultrafeine Zwischenstufe für antialiasing-empfindliche Dreiecks-/Diagrammprimitive.

## Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt bei `PolygonPath`-`points` zusätzlich `±0.000000152587890625` als 64th-/128th-yoctofeine Subpixel-Nachbarschaft.
- Die allgemeine Geometry-IR-Optimierung probt bei `PolygonPath`-`stroke_width` zusätzlich `±0.000000152587890625` als 128th-yoctofeine absolute Stroke-Width-Nachbarschaft.
- Neue Helper-Tests sichern ab, dass beide Zwischenstufen nur über den regulären Optimiererpfad und nur bei sinkendem Fehler akzeptiert werden.
- Die Änderung hängt weder an `GE1410_L` noch an eine andere Runtime-Bild-ID.

## Plan-B-/Perception-Lerneffekt

`GE1410_L` bleibt ein generalisierter Diagramm-/Dreieck-Contract mit `PolygonPath`-Primitiven. Run YD erweitert nicht die reine Bilddetektion, sondern den allgemeinen Registrierungsraum vorhandener Polygonpunkte und Polygonkonturen. Der Perception-Lerneffekt bleibt damit `generalisiert` für den nachgelagerten Optimiererpfad.

## Validierung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_points_with_sixtyfourth_yoctofine_subpixel_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_stroke_width_with_128th_yoctofine_absolute_probe` läuft grün mit `2 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py` läuft grün mit `142 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün mit `0 occurrences`.

## Ergebnis / nächster Schritt

Run YD schließt den dokumentierten GE1410_L-Feinschritt auf Code- und Testebene ab. PolygonPath-Dreiecke und -Konturen können nun eine zusätzliche ultrafeine Zwischenregistrierung nutzen. Das nächste Arbeitspaket kann in der aktiven Plan-B-Rotation zu `SE0041_1` wechseln oder weiteres allgemeines Polygon-Antialiasing-Feintuning prüfen.
