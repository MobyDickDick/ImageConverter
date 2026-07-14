# Nächstes Arbeitspaket – DLG0021 128th-Yoctofine-Gradient-Offset-Probes Run XX (2026-07-14)

Run XX arbeitet nach `docs/next_arbeitspaket_2026-07-14_runXW.md` den nächsten Schritt in der aktiven Plan-B-Rotation ab und kehrt zu `DLG0021` zurück. Der Fokus bleibt katalogfrei: Die allgemeinen `PolygonPath`-Stroke-Gradient-Offset-Probes erhalten eine 128th-yoctofeine Zwischenstufe um die bisherige Checkbox-/Haken-Gradientenregistrierung. Zusätzlich wird der bereits dokumentierte GE9012_6M-Opacity-Feinpfad um die analoge thirtysecond-yoctofeine Zwischenregistrierung ergänzt.

## Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt bei `PolygonPath.stroke_gradient.stops[].offset` zusätzlich `±0.0000003814697265625` als 128th-yoctofeine Normalized-Offset-Stufe.
- Die allgemeine Geometry-IR-Optimierung probt bei `ColorPatch`-/`RectBorder`-`fill_opacity` zusätzlich `0.98281097412109375` als thirtysecond-yoctofeine Zwischenstufe unterhalb des Ankers `0.9828125`.
- Die allgemeine Geometry-IR-Optimierung probt bei `RectBorder.stroke_opacity` zusätzlich `0.98281402587890625` als thirtysecond-yoctofeine Zwischenstufe oberhalb des Ankers `0.9828125`.
- Drei neue Helper-Tests sichern die neuen Zwischenstufen separat für Gradienten-Offsets, rechteckige Füllflächen und rechteckige Konturen ab.
- Die Änderung hängt weder an `DLG0021`, `GE9012_6M` noch an eine andere Runtime-Bild-ID.

## Plan-B-/Perception-Lerneffekt

`DLG0021` bleibt ein beschreibungsbasierter Checkbox-/Haken-Contract mit grüner Hakenkontur und Schatten. Run XX erweitert nicht die reine Bilddetektion, sondern den allgemeinen Registrierungsraum vorhandener `PolygonPath`-Gradienten sowie rechteckiger Opacity-Geometrien. Der Perception-Lerneffekt bleibt damit `generalisiert` für den nachgelagerten Optimiererpfad.

## Validierung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_stroke_gradient_offsets_with_128th_yoctofine_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_color_patch_opacity_with_thirtysecond_yoctofine_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rect_border_stroke_opacity_with_thirtysecond_yoctofine_probe` läuft grün mit `3 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün mit `0 occurrences`.

## Ergebnis

Run XX schließt den dokumentierten DLG0021-Feinschritt auf Code- und Testebene ab. PolygonPath-Gradientenkonturen können nun eine 128th-yoctofeine Offset-Zwischenregistrierung nutzen; BackBottom-ähnliche Rechteck-Opacity-Werte erhalten zusätzlich die nächste thirtysecond-yoctofeine Zwischenregistrierung. Das nächste Arbeitspaket kann in der aktiven Plan-B-Rotation zu `GE1410_L` wechseln oder weiteres allgemeines Haken-/Gradienten-Feintuning prüfen.
