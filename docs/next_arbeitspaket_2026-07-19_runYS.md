# Nächstes Arbeitspaket – GE9012_6M 256th-Yoctofine-Opacity-Probes Run YS (2026-07-19)

Run YS arbeitet nach `docs/next_arbeitspaket_2026-07-18_runYR.md` den nächsten kleinen Feinschritt in der aktiven Plan-B-Rotation ab und wechselt zu `GE9012_6M`. Der Fokus bleibt katalogfrei: Die allgemeinen `ColorPatch`-/`RectBorder`-Opacity-Probes erhalten eine weitere ultrafeine Zwischenstufe für BackBottom-ähnliche helle Rechteckflächen und Konturen.

## Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt bei `ColorPatch`-/`RectBorder`-`fill_opacity` zusätzlich `0.98281247615814208984375` als 256th-yoctofeine Zwischenstufe unterhalb des Ankers `0.9828125`.
- Die allgemeine Geometry-IR-Optimierung probt bei `RectBorder.stroke_opacity` zusätzlich `0.98281252384185791015625` als 256th-yoctofeine Zwischenstufe oberhalb des Ankers `0.9828125`.
- Neue Helper-Tests sichern ab, dass beide Zwischenstufen über den regulären Optimiererpfad akzeptiert werden, wenn sie den Fehler senken.
- Die Änderung hängt weder an `GE9012_6M` noch an eine andere Runtime-Bild-ID.

## Plan-B-/Perception-Lerneffekt

`GE9012_6M` bleibt ein beschreibungsbasierter BackBottom-/Light-Grey-Square-Contract. Run YS erweitert nicht die reine Bilddetektion, sondern den allgemeinen Registrierungsraum vorhandener Rechteckfüllungen und -konturen. Der Perception-Lerneffekt bleibt damit `nur Sonderfall` für den ursprünglichen Contract, aber `generalisiert` für den nachgelagerten Optimiererpfad.

## Validierung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_color_patch_opacity_with_256th_yoctofine_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rect_border_stroke_opacity_with_256th_yoctofine_probe` läuft grün mit `2 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün mit `0 occurrences`.

## Ergebnis / nächster Schritt

Run YS schließt den dokumentierten GE9012_6M-Feinschritt auf Code- und Testebene ab. BackBottom-ähnliche Rechteck-Opacity-Werte können nun eine zusätzliche 256th-yoctofeine Zwischenregistrierung nutzen. Das nächste Arbeitspaket kann in der aktiven Plan-B-Rotation zu `GE9013_1M` wechseln oder weiteres allgemeines Rechteck-/Opacity-Feintuning prüfen.
