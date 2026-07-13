# Nächstes Arbeitspaket – GE1410_L Thirtysecond-Yoctofine-PolygonPath-Probes Run XT (2026-07-13)

Run XT arbeitet nach `docs/next_arbeitspaket_2026-07-13_runXS.md` den nächsten Schritt in der aktiven Plan-B-Rotation ab und wechselt zu `GE1410_L`. Der Fokus bleibt katalogfrei: Die allgemeinen `PolygonPath`-Punkt- und Stroke-Width-Probes erhalten eine thirtysecond-yoctofeine Zwischenstufe für antialiasing-empfindliche Diagramm-/Dreieckskonturen.

## Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt bei `PolygonPath`-Punkten zusätzlich `±0.0000006103515625` als normalisiertes Subpixel-Delta.
- Dieselbe thirtysecond-yoctofeine Absolutstufe wird für `PolygonPath`-`stroke_width` ergänzt.
- Zwei neue Helper-Tests sichern, dass beide Zwischenstufen ausschließlich über den regulären Optimiererpfad akzeptiert werden, wenn der Fehler sinkt.
- Die Änderung hängt weder an `GE1410_L` noch an eine andere Runtime-Bild-ID.

## Plan-B-/Perception-Lerneffekt

`GE1410_L` bleibt für Achsen-/Linien- und Dreieck-Seeds generalisiert. Run XT erweitert nicht die reine Bilddetektion, sondern den allgemeinen Registrierungsraum vorhandener `PolygonPath`-Geometrien. Der Perception-Lerneffekt bleibt damit `generalisiert`.

## Validierung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_points_with_thirtysecond_yoctofine_subpixel_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_stroke_width_with_thirtysecond_yoctofine_absolute_probe` läuft grün mit `2 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün mit `0 occurrences`.

## Ergebnis / nächster Schritt

Run XT schließt den dokumentierten GE1410_L-Feinschritt auf Code- und Testebene ab. Polygonpfad-Punkte und -Strichbreiten können nun eine thirtysecond-yoctofeine Zwischenregistrierung nutzen. Das nächste Arbeitspaket kann in der aktiven Plan-B-Rotation zu `SE0041_1` wechseln oder weiteres allgemeines PolygonPath-/Antialiasing-Feintuning prüfen.
