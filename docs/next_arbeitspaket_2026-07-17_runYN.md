# Nächstes Arbeitspaket – DLG0021 512th-Yoctofine-Gradient-Offset-Probes Run YN (2026-07-17)

Run YN arbeitet nach `docs/next_arbeitspaket_2026-07-17_runYM.md` den nächsten kleinen Feinschritt in der aktiven Plan-B-Rotation ab und kehrt zu `DLG0021` zurück. Der Fokus bleibt katalogfrei: Die allgemeinen `PolygonPath`-Stroke-Gradient-Offset-Probes erhalten eine weitere ultrafeine Zwischenstufe für antialiasing-empfindliche Checkbox-/Haken-Gradienten.

## Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt bei `PolygonPath.stroke_gradient.stops[].offset` zusätzlich `±0.000000095367431640625` als normalisierte 512th-yoctofeine Zwischenstufe.
- Ein neuer Helper-Test sichert ab, dass ein bei `50.0000095367431640625%` liegender Gradient-Stop über den regulären Optimiererpfad auf `50%` zurückregistriert werden kann.
- Die Änderung hängt weder an `DLG0021` noch an eine andere Runtime-Bild-ID.

## Plan-B-/Perception-Lerneffekt

`DLG0021` bleibt ein beschreibungsbasierter Checkbox-/Haken-Contract aus `PolygonPath`-Primitiven mit grünem Stroke-Gradienten. Run YN erweitert nicht die reine Bilddetektion, sondern den allgemeinen Registrierungsraum vorhandener Stroke-Gradient-Offsets. Der Perception-Lerneffekt bleibt damit `nur Sonderfall` für den ursprünglichen Contract, aber `generalisiert` für den nachgelagerten Optimiererpfad.

## Validierung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_stroke_gradient_offsets_with_512th_yoctofine_probe` läuft grün mit `1 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün mit `0 occurrences`.

## Ergebnis / nächster Schritt

Run YN schließt den dokumentierten DLG0021-Feinschritt auf Code- und Testebene ab. PolygonPath-Gradientenkonturen können nun eine zusätzliche 512th-yoctofeine Offset-Zwischenregistrierung nutzen. Das nächste Arbeitspaket kann in der aktiven Plan-B-Rotation zu `GE1410_L` wechseln oder weiteres allgemeines Haken-/Gradienten-Feintuning prüfen.
