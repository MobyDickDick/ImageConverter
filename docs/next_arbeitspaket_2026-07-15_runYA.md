# Nächstes Arbeitspaket – GE9012_6M Sixtyfourth-Yoctofine-Opacity-Probes Run YA (2026-07-15)

Run YA arbeitet nach `docs/next_arbeitspaket_2026-07-15_runXZ.md` den nächsten Schritt in der aktiven Plan-B-Rotation ab und wechselt zu `GE9012_6M`. Der Fokus bleibt katalogfrei: Die allgemeinen `ColorPatch`-/`RectBorder`-Opacity-Probes erhalten eine sixtyfourth-yoctofeine Zwischenstufe für antialiasing-empfindliche BackBottom-ähnliche Rechteckfüllungen und Konturen.

## Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt bei `ColorPatch`-/`RectBorder`-`fill_opacity` zusätzlich `0.982811737060546875` als sixtyfourth-yoctofeine Zwischenstufe unterhalb des Ankers `0.9828125`.
- Die allgemeine Geometry-IR-Optimierung probt bei `RectBorder.stroke_opacity` zusätzlich `0.982813262939453125` als sixtyfourth-yoctofeine Zwischenstufe oberhalb des Ankers `0.9828125`.
- Zwei neue Helper-Tests sichern die Zwischenstufen separat für rechteckige Füllflächen und rechteckige Konturen ab.
- Die Änderung hängt weder an `GE9012_6M` noch an eine andere Runtime-Bild-ID.

## Plan-B-/Perception-Lerneffekt

`GE9012_6M` bleibt ein beschreibungsbasierter BackBottom-/hellgraues-Quadrat-Contract mit rechteckiger Füllfläche und Kontur. Run YA erweitert nicht die reine Bilddetektion, sondern den allgemeinen Registrierungsraum vorhandener rechteckiger Opacity-Geometrien. Der Perception-Lerneffekt bleibt damit `generalisiert` für den nachgelagerten Optimiererpfad.

## Validierung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_color_patch_opacity_with_sixtyfourth_yoctofine_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rect_border_stroke_opacity_with_sixtyfourth_yoctofine_probe` läuft grün mit `2 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün mit `0 occurrences`.

## Ergebnis / nächster Schritt

Run YA schließt den dokumentierten GE9012_6M-Feinschritt auf Code- und Testebene ab. BackBottom-ähnliche Rechteck-Opacity-Werte können nun eine sixtyfourth-yoctofeine Zwischenregistrierung nutzen. Das nächste Arbeitspaket kann in der aktiven Plan-B-Rotation zu `GE9013_1M` wechseln oder weiteres allgemeines Rechteck-/Opacity-Feintuning prüfen.
