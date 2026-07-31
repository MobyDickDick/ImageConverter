# Nächstes Arbeitspaket – GE9013_1M 67108864th-Yoctofine-Opacity-Probes Run AAG (2026-07-28)

Run AAG arbeitet nach `docs/next_arbeitspaket_2026-07-28_runAAF.md` den nächsten Schritt in der aktiven Plan-B-Rotation ab und wechselt zu `GE9013_1M`. Der Fokus bleibt katalogfrei: Die allgemeinen `ColorPatch`- und `RectBorder`-Opacity-Probes erhalten eine 67108864th-yoctofeine Zwischenstufe direkt um die bisherige BackBottom-Zielopacity.

## Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt bei `ColorPatch.fill_opacity` und `RectBorder.fill_opacity` zusätzlich `0.98281249999927240423858165740966796875`.
- Für `ColorPatch.stroke_opacity` und `RectBorder.stroke_opacity` wird spiegelbildlich `0.98281250000072759576141834259033203125` geprüft.
- Neue Helper-Tests sichern, dass der reguläre Optimiererpfad die neuen Zwischenstufen nur bei sinkendem Fehler akzeptiert.
- Die Änderung hängt weder an `GE9013_1M` noch an einer anderen Runtime-Bild-ID.

## Plan-B-/Perception-Lerneffekt

`GE9013_1M` bleibt ein beschreibungsbasierter BackBottom-/Light-Grey-Square-Contract. Run AAG erweitert nicht die reine Bilddetektion, sondern den allgemeinen Opacity-Registrierungsraum für vorhandene Rechteckflächen und -konturen. Der Perception-Lerneffekt bleibt auf Seed-Ebene `nur Sonderfall`; die nachgelagerte Opacity-Feinregistrierung ist katalogfrei generalisiert.

## Validierung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_color_patch_opacity_with_67108864th_yoctofine_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rect_border_stroke_opacity_with_67108864th_yoctofine_probe` läuft grün mit `2 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün mit `0 occurrences`.

## Ergebnis / nächster Schritt

Run AAG schließt den dokumentierten GE9013_1M-Feinschritt auf Code- und Helper-Test-Ebene ab. Rechteckige Füll- und Konturelemente können nun eine zusätzliche 67108864th-yoctofeine Opacity-Zwischenregistrierung nutzen. Das nächste Arbeitspaket kann in der aktiven Plan-B-Rotation wieder zu `DLG0021` wechseln oder weiteres allgemeines Gradienten-/Opacity-Feintuning prüfen.
