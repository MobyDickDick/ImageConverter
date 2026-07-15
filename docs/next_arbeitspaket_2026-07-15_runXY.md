# Nächstes Arbeitspaket – GE1410_L Sixtyfourth-Yoctofine-PolygonPath-Probes Run XY (2026-07-15)

Run XY arbeitet nach `docs/next_arbeitspaket_2026-07-14_runXX.md` den nächsten Schritt in der aktiven Plan-B-Rotation ab und wechselt zu `GE1410_L`. Der Fokus bleibt katalogfrei: Die allgemeinen `PolygonPath`-Punkt- und Stroke-Width-Probes erhalten eine sixtyfourth-yoctofeine Zwischenstufe für antialiasing-empfindliche Diagramm-/Dreieckskonturen.

## Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt bei `PolygonPath`-Punkten zusätzlich `±0.00000030517578125` als normalisiertes Subpixel-Delta.
- Dieselbe sixtyfourth-yoctofeine Absolutstufe wird für `PolygonPath`-`stroke_width` ergänzt.
- Zwei neue Helper-Tests sichern, dass beide Zwischenstufen ausschließlich über den regulären Optimiererpfad akzeptiert werden, wenn der Fehler sinkt.
- Die Änderung hängt weder an `GE1410_L` noch an eine andere Runtime-Bild-ID.

## Plan-B-/Perception-Lerneffekt

`GE1410_L` bleibt für Achsen-/Linien- und Dreieck-Seeds generalisiert. Run XY erweitert nicht die reine Bilddetektion, sondern den allgemeinen Registrierungsraum vorhandener `PolygonPath`-Geometrien. Der Perception-Lerneffekt bleibt damit `generalisiert`.

## Validierung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_points_with_sixtyfourth_yoctofine_subpixel_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_stroke_width_with_sixtyfourth_yoctofine_absolute_probe` läuft grün mit `2 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün mit `0 occurrences`.

## Ergebnis / nächster Schritt

Run XY schließt den dokumentierten GE1410_L-Feinschritt auf Code- und Testebene ab. Polygonpfad-Punkte und -Strichbreiten können nun eine sixtyfourth-yoctofeine Zwischenregistrierung nutzen. Das nächste Arbeitspaket kann in der aktiven Plan-B-Rotation zu `SE0041_1` wechseln oder weiteres allgemeines PolygonPath-/Antialiasing-Feintuning prüfen.
