# Nächstes Arbeitspaket – GE9012_6M 128th-Yoctofine-Opacity-Probes Run YJ (2026-07-17)

Run YJ arbeitet nach `docs/next_arbeitspaket_2026-07-16_runYI.md` den nächsten kleinen Feinschritt in der aktiven Plan-B-Rotation ab und wechselt zu `GE9012_6M`. Der Fokus bleibt katalogfrei: Die allgemeinen `ColorPatch`-/`RectBorder`-Opacity-Probes erhalten eine weitere ultrafeine Zwischenstufe für antialiasing-empfindliche BackBottom-ähnliche Rechteckfüllungen und Konturen.

## Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt bei `ColorPatch`-/`RectBorder`-`fill_opacity` zusätzlich `0.9828121185302734375` als 128th-yoctofeine Zwischenstufe unterhalb des Ankers `0.9828125`.
- Die allgemeine Geometry-IR-Optimierung probt bei `RectBorder.stroke_opacity` zusätzlich `0.9828128814697265625` als 128th-yoctofeine Zwischenstufe oberhalb des Ankers `0.9828125`.
- Neue Helper-Tests sichern ab, dass beide Zwischenstufen nur über den regulären Optimiererpfad und nur bei sinkendem Fehler akzeptiert werden.
- Die Änderung hängt weder an `GE9012_6M` noch an eine andere Runtime-Bild-ID.

## Plan-B-/Perception-Lerneffekt

`GE9012_6M` bleibt ein beschreibungsbasierter BackBottom-/Light-Grey-Square-Contract aus `ColorPatch`- und `RectBorder`-Primitiven. Run YJ erweitert nicht die reine Bilddetektion, sondern den allgemeinen Registrierungsraum vorhandener Rechteck-Opacity-Werte. Der Perception-Lerneffekt bleibt damit `nur Sonderfall` für den ursprünglichen Contract, aber `generalisiert` für den nachgelagerten Optimiererpfad.

## Validierung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_color_patch_opacity_with_128th_yoctofine_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rect_border_stroke_opacity_with_128th_yoctofine_probe` läuft grün mit `2 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün mit `0 occurrences`.

## Ergebnis / nächster Schritt

Run YJ schließt den dokumentierten GE9012_6M-Feinschritt auf Code- und Testebene ab. BackBottom-ähnliche Rechteck-Opacity-Werte können nun eine zusätzliche 128th-yoctofeine Zwischenregistrierung nutzen. Das nächste Arbeitspaket kann in der aktiven Plan-B-Rotation zu `GE9013_1M` wechseln oder weiteres allgemeines Rechteck-/Opacity-Feintuning prüfen.
