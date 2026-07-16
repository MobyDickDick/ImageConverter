# Nächstes Arbeitspaket – SE0041_1 256th-Yoctofine-RectRule-Stroke-Probes Run YG (2026-07-16)

Run YG arbeitet nach `docs/next_arbeitspaket_2026-07-16_runYF.md` den nächsten Schritt in der aktiven Plan-B-Rotation ab und wechselt zurück zu `SE0041_1`. Der Fokus bleibt katalogfrei: Die allgemeinen `RectBorder`-, `HorizontalRule`- und `VerticalRule`-Stroke-Width-Probes erhalten die nächste ultrafeine Zwischenstufe für antialiasing-empfindliche Square-Badge-Rechteck-/Linienkonturen.

## Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt bei `RectBorder`-, `HorizontalRule`- und `VerticalRule`-`stroke_width` zusätzlich `±0.0000000762939453125` als 256th-yoctofeine absolute Stroke-Width-Nachbarschaft.
- Neue Helper-Tests sichern ab, dass die Zwischenstufe sowohl für `RectBorder` als auch für Rule-Primitive nur über den regulären Optimiererpfad und nur bei sinkendem Fehler akzeptiert wird.
- Die Änderung hängt weder an `SE0041_1` noch an eine andere Runtime-Bild-ID.

## Plan-B-/Perception-Lerneffekt

`SE0041_1` bleibt ein beschreibungsbasierter Square-Badge-Contract aus `RectBorder`-, `ColorPatch`- und Rule-Primitiven. Run YG erweitert nicht die reine Bilddetektion, sondern den allgemeinen Registrierungsraum vorhandener Rechteckkonturen und Linienkonturen. Der Perception-Lerneffekt bleibt damit `nur Sonderfall` für die manuelle Seed-Annahme, aber `generalisiert` für den nachgelagerten Optimiererpfad.

## Validierung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rect_border_stroke_width_with_256th_yoctofine_absolute_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rule_stroke_width_with_256th_yoctofine_absolute_probe` läuft grün mit `2 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py` läuft grün mit `148 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün mit `0 occurrences`.

## Ergebnis / nächster Schritt

Run YG schließt den dokumentierten SE0041_1-Feinschritt auf Code- und Testebene ab. Rechteck- und Linienkonturen können nun eine zusätzliche 256th-yoctofeine Stroke-Width-Zwischenregistrierung nutzen. Das nächste Arbeitspaket kann in der aktiven Plan-B-Rotation weitergeführt werden oder weiteres allgemeines Rect-/Rule-Antialiasing-Feintuning prüfen.
