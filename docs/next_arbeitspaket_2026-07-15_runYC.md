# Nächstes Arbeitspaket – DLG0021 256th-Yoctofine-Gradient-Offset-Probes Run YC (2026-07-15)

Run YC arbeitet nach `docs/next_arbeitspaket_2026-07-15_runYB.md` den nächsten Schritt in der aktiven Plan-B-Rotation ab und kehrt zu `DLG0021` zurück. Der Fokus bleibt katalogfrei: Die allgemeinen `PolygonPath`-Stroke-Gradient-Offset-Probes erhalten eine 256th-yoctofeine Zwischenstufe um die bisherige Checkbox-/Haken-Gradientenregistrierung.

## Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt bei `PolygonPath`-`stroke_gradient`-Stops zusätzlich `±0.00000019073486328125` Prozentpunkte als 256th-yoctofeine Offset-Nachbarschaft.
- Ein neuer Helper-Test sichert ab, dass die Zwischenstufe nur über den regulären Optimiererpfad und nur bei sinkendem Fehler akzeptiert wird.
- Die Änderung hängt weder an `DLG0021` noch an eine andere Runtime-Bild-ID.

## Plan-B-/Perception-Lerneffekt

`DLG0021` bleibt ein beschreibungsbasierter Checkbox-/Haken-Contract mit grüner Hakenkontur und Schatten. Run YC erweitert nicht die reine Bilddetektion, sondern den allgemeinen Registrierungsraum vorhandener `PolygonPath`-Gradientenkonturen. Der Perception-Lerneffekt bleibt damit `generalisiert` für den nachgelagerten Optimiererpfad.

## Validierung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_stroke_gradient_offsets_with_256th_yoctofine_probe` läuft grün mit `1 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün mit `0 occurrences`.

## Ergebnis / nächster Schritt

Run YC schließt den dokumentierten DLG0021-Feinschritt auf Code- und Testebene ab. PolygonPath-Gradientenkonturen können nun eine 256th-yoctofeine Offset-Zwischenregistrierung nutzen. Das nächste Arbeitspaket kann in der aktiven Plan-B-Rotation zu `GE1410_L` wechseln oder weiteres allgemeines Haken-/Gradienten-Feintuning prüfen.
