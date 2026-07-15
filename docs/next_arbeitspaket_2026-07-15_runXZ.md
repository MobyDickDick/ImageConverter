# Nächstes Arbeitspaket – SE0041_1 Eighth-Yoctofine-Rule-Stroke-Probes Run XZ (2026-07-15)

Run XZ arbeitet nach `docs/next_arbeitspaket_2026-07-15_runXY.md` den nächsten Schritt in der aktiven Plan-B-Rotation ab und wechselt zu `SE0041_1`. Der Fokus bleibt katalogfrei: Die allgemeinen `RectBorder`-/`HorizontalRule`-/`VerticalRule`-Stroke-Width-Probes erhalten eine eighth-yoctofeine absolute Zwischenstufe für antialiasing-empfindliche Square-Badge-Konturen.

## Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt bei `RectBorder`, `HorizontalRule` und `VerticalRule`-`stroke_width` zusätzlich `±0.0000006103515625` als eighth-yoctofeine absolute Stufe zwischen der quarter-yoctofeinen Stufe und dem unveränderten Ausgangswert.
- Zwei neue Helper-Tests sichern die Zwischenstufe für rechteckige Konturen und Rule-Primitive ab.
- Die Änderung hängt weder an `SE0041_1` noch an eine andere Runtime-Bild-ID.

## Plan-B-/Perception-Lerneffekt

`SE0041_1` bleibt ein beschreibungsbasierter Square-Badge-Contract mit roter Viereck-Kopfkontur, senkrechtem Stem und waagrechtem Arm. Run XZ erweitert nicht die reine Bilddetektion, sondern den allgemeinen Registrierungsraum vorhandener `RectBorder`-/Rule-Stroke-Geometrien. Der Perception-Lerneffekt bleibt damit `generalisiert`.

## Validierung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rect_border_stroke_width_with_eighth_yoctofine_absolute_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rule_stroke_width_with_eighth_yoctofine_absolute_probe` läuft grün mit `2 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün mit `0 occurrences`.

## Ergebnis / nächster Schritt

Run XZ schließt den dokumentierten SE0041_1-Feinschritt auf Code- und Testebene ab. Rule- und RectBorder-Strichbreiten können nun eine eighth-yoctofeine absolute Zwischenregistrierung nutzen. Das nächste Arbeitspaket kann in der aktiven Plan-B-Rotation zu `GE9012_6M` wechseln oder weiteres allgemeines Rule-/RectBorder-Antialiasing-Feintuning prüfen.
