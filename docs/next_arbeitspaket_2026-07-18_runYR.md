# Nächstes Arbeitspaket – SE0041_1 2048th-Yoctofine-Rule-/RectBorder-Stroke-Probes Run YR (2026-07-18)

Run YR arbeitet nach `docs/next_arbeitspaket_2026-07-18_runYQ.md` den nächsten kleinen Feinschritt in der aktiven Plan-B-Rotation ab und wechselt zu `SE0041_1`. Der Fokus bleibt katalogfrei: Die allgemeinen `RectBorder`-, `HorizontalRule`- und `VerticalRule`-Stroke-Width-Probes erhalten eine weitere ultrafeine Zwischenstufe für antialiasing-empfindliche Square-Badge-Konturen und -Stems.

## Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt bei `RectBorder.stroke_width`, `HorizontalRule.stroke_width` und `VerticalRule.stroke_width` zusätzlich `±0.0000000095367431640625` als absolute 2048th-yoctofeine Stroke-Width-Zwischenstufe.
- Neue Helper-Tests sichern ab, dass sowohl `RectBorder`- als auch Rule-Primitive die Zwischenstufe über den regulären Optimiererpfad akzeptieren, wenn sie den Fehler senkt.
- Die Änderung hängt weder an `SE0041_1` noch an eine andere Runtime-Bild-ID.

## Plan-B-/Perception-Lerneffekt

`SE0041_1` bleibt ein beschreibungsbasierter Square-Badge-Contract aus roter Kopfkachel, grauer Kontur und neutralen Rule-/Stem-Primitiven. Run YR erweitert nicht die reine Bilddetektion, sondern den allgemeinen Registrierungsraum vorhandener Rechteck- und Linienkonturen. Der Perception-Lerneffekt bleibt damit `nur Sonderfall` für den ursprünglichen Contract, aber `generalisiert` für den nachgelagerten Optimiererpfad.

## Validierung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rect_border_stroke_width_with_2048th_yoctofine_absolute_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rule_stroke_width_with_2048th_yoctofine_absolute_probe` läuft grün mit `2 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün mit `0 occurrences`.

## Ergebnis / nächster Schritt

Run YR schließt den dokumentierten SE0041_1-Feinschritt auf Code- und Testebene ab. Rule- und RectBorder-Konturbreiten können nun eine zusätzliche 2048th-yoctofeine Zwischenregistrierung nutzen. Das nächste Arbeitspaket kann in der aktiven Plan-B-Rotation zu `GE9012_6M` wechseln oder weiteres allgemeines Square-Badge-/Stroke-Antialiasing-Feintuning prüfen.
