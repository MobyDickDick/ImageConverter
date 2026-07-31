# Nächstes Arbeitspaket – SE0041_1 8388608th-Yoctofine-Stroke-Width-Probes Run ABD (2026-07-31)

Run ABD arbeitet nach `docs/next_arbeitspaket_2026-07-31_runABC.md` den nächsten Schritt in der aktiven Plan-B-Rotation ab und wechselt zu `SE0041_1`. Der Fokus bleibt katalogfrei: Die allgemeinen absoluten Stroke-Width-Probes für `RectBorder`, `HorizontalRule` und `VerticalRule` erhalten eine 8388608th-yoctofeine Zwischenstufe für antialiasingempfindliche Kachelkonturen und Linien.

## Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt bei `RectBorder`, `HorizontalRule` und `VerticalRule` zusätzlich `±0.0000000000023283064365386962890625` für `stroke_width`.
- Neue Helper-Tests sichern, dass der reguläre Optimiererpfad die neue 8388608th-yoctofeine Zwischenstufe sowohl für Rechteckkonturen als auch für Regeln nur bei sinkendem Fehler akzeptiert.
- Die Änderung hängt weder an `SE0041_1` noch an einer anderen Runtime-Bild-ID.

## Plan-B-/Perception-Lerneffekt

`SE0041_1` bleibt ein beschreibungsbasierter Square-Badge-Contract. Run ABD erweitert nicht die reine Bilddetektion, sondern den allgemeinen Registrierungsraum für vorhandene Rechteck- und Linienprimitive. Der Perception-Lerneffekt bleibt auf Seed-Ebene `nur Sonderfall`; die nachgelagerte Kontur-Feinregistrierung ist katalogfrei generalisiert.

## Validierung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rect_border_stroke_width_with_8388608th_yoctofine_absolute_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rule_stroke_width_with_8388608th_yoctofine_absolute_probe` läuft grün mit `2 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün mit `0 occurrences`.

## Ergebnis / nächster Schritt

Run ABD schließt den dokumentierten SE0041_1-Feinschritt auf Code- und Helper-Test-Ebene ab. Rechteckkonturen und Regeln können nun eine zusätzliche 8388608th-yoctofeine Stroke-Width-Zwischenregistrierung nutzen. Das nächste Arbeitspaket kann in der aktiven Plan-B-Rotation zu `GE9012_6M` wechseln oder weiteres allgemeines Kontur-/Stem-Feintuning prüfen.
