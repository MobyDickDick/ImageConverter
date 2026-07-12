# Nächstes Arbeitspaket – GE9012_6M Eighth-Yoctofine-Opacity-Probes Run XQ (2026-07-12)

Run XQ arbeitet nach `docs/next_arbeitspaket_2026-07-12_runXP.md` den nächsten Schritt in der aktiven Plan-B-Rotation ab und kehrt zu `GE9012_6M` zurück. Der Fokus bleibt katalogfrei: Die allgemeinen `ColorPatch`- und `RectBorder`-Opacity-Probes erhalten eine eighth-yoctofeine Zwischenstufe nahe der bisherigen BackBottom-Zielopacity.

## Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt bei `ColorPatch.fill_opacity` zusätzlich `0.982806396484375` als eighth-yoctofeine Zwischenstufe unterhalb von `0.9828125`.
- Die allgemeine Geometry-IR-Optimierung probt bei `RectBorder.stroke_opacity` zusätzlich `0.982818603515625` als eighth-yoctofeine Zwischenstufe oberhalb von `0.9828125`.
- Zwei Detailtests sichern die neuen Opacity-Probes separat für rechteckige Füllflächen und Konturen ab.
- Die Änderung hängt weder an `GE9012_6M` noch an eine andere Runtime-Bild-ID.

## Plan-B-/Perception-Lerneffekt

`GE9012_6M` bleibt ein beschreibungsbasierter BackBottom-/hellgraues-Quadrat-Contract. Run XQ erweitert nicht die reine Bilddetektion, sondern den allgemeinen Registrierungsraum für vorhandene rechteckige Füll- und Konturelemente. Der Perception-Lerneffekt bleibt auf Ebene der Seed-Quelle `nur Sonderfall`; die nachgelagerte Opacity-Registrierung ist weiterhin katalogfrei generalisiert.

## Validierung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_color_patch_opacity_with_eighth_yoctofine_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rect_border_stroke_opacity_with_eighth_yoctofine_probe` läuft grün mit `2 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün mit `0 occurrences`.

## Ergebnis / nächster Schritt

Run XQ schließt den dokumentierten GE9012_6M-Feinschritt auf Code- und Testebene ab. Rechteckige Füll- und Konturelemente können nun eine eighth-yoctofeine Opacity-Zwischenregistrierung nutzen. Das nächste Arbeitspaket kann in der aktiven Plan-B-Rotation zu `GE9013_1M` wechseln oder weiteres allgemeines BackBottom-/Rechteck-Feintuning prüfen.
