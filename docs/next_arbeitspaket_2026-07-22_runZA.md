# Nächstes Arbeitspaket – SE0041_1 4096th-Yoctofine-Rule-Stroke-Probes Run ZA (2026-07-22)

Run ZA arbeitet nach `docs/next_arbeitspaket_2026-07-22_runYZ.md` den nächsten Schritt in der aktiven Plan-B-Rotation ab und wechselt zu `SE0041_1`. Der Fokus bleibt katalogfrei: Die allgemeinen `RectBorder`-, `HorizontalRule`- und `VerticalRule`-Stroke-Width-Probes erhalten eine 4096th-yoctofeine Zwischenstufe für antialiasingempfindliche Square-Badge-Konturen und Stem-/Arm-Linien.

## Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt bei `RectBorder.stroke_width`, `HorizontalRule.stroke_width` und `VerticalRule.stroke_width` zusätzlich `±0.00000000476837158203125` neben den bereits vorhandenen feinen absoluten Stroke-Stufen.
- Neue Helper-Tests sichern, dass der reguläre Optimiererpfad die neue 4096th-yoctofeine Zwischenstufe für Rechteckkonturen und Rules nur bei sinkendem Fehler akzeptiert.
- Die Änderung hängt weder an `SE0041_1` noch an eine andere Runtime-Bild-ID.

## Plan-B-/Perception-Lerneffekt

`SE0041_1` bleibt ein beschreibungsbasierter Square-Badge-Contract. Run ZA erweitert nicht die reine Bilddetektion, sondern den allgemeinen Registrierungsraum für vorhandene Rechteckkonturen sowie horizontale und vertikale Rule-Elemente. Der Perception-Lerneffekt bleibt auf Seed-Ebene `nur Sonderfall`; die nachgelagerte Rule-/RectBorder-Feinregistrierung ist katalogfrei generalisiert.

## Validierung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rect_border_stroke_width_with_4096th_yoctofine_absolute_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rule_stroke_width_with_4096th_yoctofine_absolute_probe` läuft grün mit `2 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün mit `0 occurrences`.

## Ergebnis / nächster Schritt

Run ZA schließt den dokumentierten SE0041_1-Feinschritt auf Code- und Helper-Test-Ebene ab. Rule- und RectBorder-Strichbreiten können nun eine zusätzliche 4096th-yoctofeine absolute Zwischenregistrierung nutzen. Das nächste Arbeitspaket kann in der aktiven Plan-B-Rotation weitergeführt werden oder weiteres allgemeines Square-Badge-Antialiasing-Feintuning prüfen.
