# Nächstes Arbeitspaket – SE0041_1 131072nd-Yoctofine-Rule-/RectBorder-Stroke-Probes Run ZZ (2026-07-27)

Run ZZ arbeitet nach `docs/next_arbeitspaket_2026-07-27_runZY.md` den nächsten Schritt in der aktiven Plan-B-Rotation ab und wechselt zu `SE0041_1`. Der Fokus bleibt katalogfrei: Die allgemeinen `RectBorder`-, `HorizontalRule`- und `VerticalRule`-Stroke-Width-Probes erhalten eine 131072nd-yoctofeine Zwischenstufe für antialiasingempfindliche Square-Badge- und Rule-Konturen.

## Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt bei `RectBorder.stroke_width`, `HorizontalRule.stroke_width` und `VerticalRule.stroke_width` zusätzlich `±0.0000000001490116119384765625` neben den bereits vorhandenen feinen absoluten Stroke-Stufen.
- Neue Helper-Tests sichern, dass der reguläre Optimiererpfad die neue 131072nd-yoctofeine Zwischenstufe für Rechteck- und Rule-Konturen nur bei sinkendem Fehler akzeptiert.
- Die Änderung hängt weder an `SE0041_1` noch an einer anderen Runtime-Bild-ID.

## Plan-B-/Perception-Lerneffekt

`SE0041_1` bleibt ein beschreibungsbasierter Square-Badge-Contract. Run ZZ erweitert nicht die reine Bilddetektion, sondern den allgemeinen Registrierungsraum für vorhandene Rechteck- und Rule-Konturen. Der Perception-Lerneffekt bleibt auf Seed-Ebene `nur Sonderfall`; die nachgelagerte Kontur-Feinregistrierung ist katalogfrei generalisiert.

## Validierung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rect_border_stroke_width_with_131072nd_yoctofine_absolute_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rule_stroke_width_with_131072nd_yoctofine_absolute_probe` läuft grün mit `2 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün mit `0 occurrences`.

## Ergebnis / nächster Schritt

Run ZZ schließt den dokumentierten SE0041_1-Feinschritt auf Code- und Helper-Test-Ebene ab. Rechteck- und Rule-Konturen können nun eine zusätzliche 131072nd-yoctofeine Stroke-Width-Zwischenregistrierung nutzen. Das nächste Arbeitspaket kann in der aktiven Plan-B-Rotation zu `GE9012_6M` wechseln oder weiteres allgemeines Rechteck-/BackBottom-Antialiasing-Feintuning prüfen.
