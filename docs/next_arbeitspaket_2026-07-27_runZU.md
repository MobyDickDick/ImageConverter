# Nächstes Arbeitspaket – SE0041_1 65536th-Yoctofine-Rule-/RectBorder-Stroke-Probes Run ZU (2026-07-27)

Run ZU arbeitet nach `docs/next_arbeitspaket_2026-07-27_runZT.md` den nächsten Schritt in der aktiven Plan-B-Rotation ab und wechselt zu `SE0041_1`. Der Fokus bleibt katalogfrei: Die allgemeinen `RectBorder`-, `HorizontalRule`- und `VerticalRule`-Stroke-Width-Probes erhalten eine 65536th-yoctofeine Zwischenstufe für antialiasingempfindliche Square-Badge- und Rule-Konturen.

## Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt bei `RectBorder.stroke_width`, `HorizontalRule.stroke_width` und `VerticalRule.stroke_width` zusätzlich `±0.000000000298023223876953125` neben den bereits vorhandenen feinen absoluten Stroke-Stufen.
- Neue Helper-Tests sichern, dass der reguläre Optimiererpfad die neue 65536th-yoctofeine Zwischenstufe für Rechteck- und Rule-Konturen nur bei sinkendem Fehler akzeptiert.
- Die Änderung hängt weder an `SE0041_1` noch an einer anderen Runtime-Bild-ID.

## Plan-B-/Perception-Lerneffekt

`SE0041_1` bleibt ein beschreibungsbasierter Square-Badge-Contract. Run ZU erweitert nicht die reine Bilddetektion, sondern den allgemeinen Registrierungsraum für vorhandene Rechteck- und Rule-Konturen. Der Perception-Lerneffekt bleibt auf Seed-Ebene `nur Sonderfall`; die nachgelagerte Kontur-Feinregistrierung ist katalogfrei generalisiert.

## Validierung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rect_border_stroke_width_with_65536th_yoctofine_absolute_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rule_stroke_width_with_65536th_yoctofine_absolute_probe` läuft grün mit `2 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün mit `0 occurrences`.

## Ergebnis / nächster Schritt

Run ZU schließt den dokumentierten SE0041_1-Feinschritt auf Code- und Helper-Test-Ebene ab. Rechteck- und Rule-Konturen können nun eine zusätzliche 65536th-yoctofeine Stroke-Width-Zwischenregistrierung nutzen. Das nächste Arbeitspaket kann in der aktiven Plan-B-Rotation zu `GE9012_6M` wechseln oder weiteres allgemeines Rechteck-/BackBottom-Antialiasing-Feintuning prüfen.
