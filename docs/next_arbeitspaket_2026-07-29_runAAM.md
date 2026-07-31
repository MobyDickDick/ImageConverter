# Nächstes Arbeitspaket – DLG0021 262144th-Yoctofine-Gradient-Offset-Probes Run AAM (2026-07-29)

Run AAM arbeitet nach `docs/next_arbeitspaket_2026-07-29_runAAL.md` den nächsten Schritt in der aktiven Plan-B-Rotation ab und kehrt zu `DLG0021` zurück. Der Fokus bleibt katalogfrei: Die allgemeinen `PolygonPath`-Stroke-Gradient-Offset-Probes erhalten eine 262144th-yoctofeine Zwischenstufe um die bisherige Checkbox-/Haken-Gradientenregistrierung.

## Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt bei `PolygonPath.stroke_gradient.stops[].offset` zusätzlich `±0.000000000186264514923095703125` als 262144th-yoctofeine Zwischenregistrierung.
- Ein neuer Helper-Test sichert, dass ein Offset von `50.0000000186264514923095703125%` über den regulären Optimiererpfad auf `50%` zurückregistriert und nur bei sinkendem Fehler akzeptiert wird.
- Die Änderung hängt weder an `DLG0021` noch an einer anderen Runtime-Bild-ID.

## Plan-B-/Perception-Lerneffekt

`DLG0021` bleibt ein beschreibungsbasierter Checkbox-/Haken-Contract. Run AAM erweitert nicht die reine Bilddetektion, sondern den allgemeinen Registrierungsraum für vorhandene `PolygonPath`-Stroke-Gradienten. Der Perception-Lerneffekt bleibt auf Seed-Ebene `nur Sonderfall`; die nachgelagerte Gradienten-Feinregistrierung ist katalogfrei generalisiert.

## Validierung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_stroke_gradient_offsets_with_262144th_yoctofine_probe` läuft grün mit `1 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün mit `0 occurrences`.

## Ergebnis / nächster Schritt

Run AAM schließt den dokumentierten DLG0021-Feinschritt auf Code- und Helper-Test-Ebene ab. Polygonpfad-Stroke-Gradienten können nun eine zusätzliche 262144th-yoctofeine Offset-Zwischenregistrierung nutzen. Das nächste Arbeitspaket kann in der aktiven Plan-B-Rotation zu `GE1410_L` wechseln oder weiteres allgemeines PolygonPath-Antialiasing-/Kontur-Feintuning prüfen.
