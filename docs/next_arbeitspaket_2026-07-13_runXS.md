# Nächstes Arbeitspaket – DLG0021 Sixtyfourth-Yoctofine-Stroke-Gradient-Offset-Probes Run XS (2026-07-13)

Run XS arbeitet nach `docs/next_arbeitspaket_2026-07-12_runXR.md` den nächsten Schritt in der aktiven Plan-B-Rotation ab und kehrt zu `DLG0021` zurück. Der Fokus bleibt katalogfrei: Die allgemeinen `PolygonPath`-Stroke-Gradient-Offset-Probes erhalten eine sixtyfourth-yoctofeine Zwischenstufe um die bisherige Checkbox-/Haken-Gradientenregistrierung.

## Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt bei `PolygonPath.stroke_gradient.stops[].offset` zusätzlich `±0.000000762939453125` als sixtyfourth-yoctofeine Offset-Stufe.
- Ein neuer Helper-Test sichert, dass ein minimal um `0.0000762939453125%` verschobener Gradient-Stop über den regulären Optimiererpfad wieder auf `50%` registriert wird.
- Die Änderung hängt weder an `DLG0021` noch an eine andere Runtime-Bild-ID.

## Plan-B-/Perception-Lerneffekt

`DLG0021` bleibt ein beschreibungsbasierter Checkbox-/Haken-Contract. Run XS erweitert nicht die reine Bilddetektion, sondern den allgemeinen Registrierungsraum für vorhandene `PolygonPath`-Gradientenkonturen. Der Perception-Lerneffekt bleibt auf Ebene der Seed-Quelle `nur Sonderfall`; die nachgelagerte Stroke-Gradient-Offset-Registrierung ist weiterhin katalogfrei generalisiert.

## Validierung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_stroke_gradient_offsets_with_sixtyfourth_yoctofine_probe` läuft grün mit `1 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün mit `0 occurrences`.

## Ergebnis / nächster Schritt

Run XS schließt den dokumentierten DLG0021-Feinschritt auf Code- und Testebene ab. PolygonPath-Gradientenkonturen können nun eine sixtyfourth-yoctofeine Offset-Zwischenregistrierung nutzen. Das nächste Arbeitspaket kann in der aktiven Plan-B-Rotation zu `GE1410_L` wechseln oder weiteres allgemeines Haken-/Gradienten-Feintuning prüfen.
