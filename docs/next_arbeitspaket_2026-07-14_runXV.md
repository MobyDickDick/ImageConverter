# Nächstes Arbeitspaket – GE9012_6M Sixteenth-Yoctofine-Opacity-Probes Run XV (2026-07-14)

Run XV arbeitet nach `docs/next_arbeitspaket_2026-07-14_runXU.md` den nächsten Schritt in der aktiven Plan-B-Rotation ab und wechselt zu `GE9012_6M`. Der Fokus bleibt katalogfrei: Die allgemeinen `ColorPatch`-/`RectBorder`-Opacity-Probes erhalten die nächste sixteenth-yoctofeine Zwischenstufe für BackBottom-ähnliche helle Rechteckflächen und Konturen.

## Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt bei `ColorPatch`- und `RectBorder`-`fill_opacity` zusätzlich `0.9828094482421875` als sixteenth-yoctofeine Zwischenstufe zwischen der vorhandenen eighth-yoctofeinen Füllprobe und dem Ausgangsanker `0.9828125`.
- Die allgemeine Geometry-IR-Optimierung probt bei `RectBorder`-`stroke_opacity` zusätzlich `0.9828155517578125` als sixteenth-yoctofeine Zwischenstufe zwischen dem Ausgangsanker `0.9828125` und der vorhandenen eighth-yoctofeinen Konturprobe.
- Zwei neue Helper-Tests sichern die neue Zwischenstufe separat für rechteckige Füllflächen und Konturen ab.
- Die Änderung hängt weder an `GE9012_6M` noch an eine andere Runtime-Bild-ID.

## Plan-B-/Perception-Lerneffekt

`GE9012_6M` bleibt ein beschreibungsbasierter BackBottom-/hellgraues-Quadrat-Contract mit rechteckiger Füllfläche und Kontur. Run XV erweitert nicht die reine Bilddetektion, sondern den allgemeinen Registrierungsraum vorhandener `ColorPatch`-/`RectBorder`-Opacity-Geometrien. Der Perception-Lerneffekt bleibt damit `generalisiert` für den nachgelagerten Optimiererpfad.

## Validierung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_color_patch_opacity_with_sixteenth_yoctofine_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rect_border_stroke_opacity_with_sixteenth_yoctofine_probe` läuft grün mit `2 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün mit `0 occurrences`.

## Ergebnis

Run XV schließt den dokumentierten GE9012_6M-Feinschritt auf Code- und Testebene ab. ColorPatch- und RectBorder-Deckkraftwerte können nun eine sixteenth-yoctofeine Zwischenregistrierung nutzen. Das nächste Arbeitspaket kann in der aktiven Plan-B-Rotation zu `GE9013_1M` wechseln oder weiteres allgemeines BackBottom-/Opacity-Feintuning prüfen.
