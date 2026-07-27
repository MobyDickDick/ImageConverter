# Nächstes Arbeitspaket – GE9012_6M 8388608th-Yoctofine-Opacity-Probes Run AAA (2026-07-27)

Run AAA arbeitet nach `docs/next_arbeitspaket_2026-07-27_runZZ.md` den nächsten Schritt in der aktiven Plan-B-Rotation ab und wechselt zu `GE9012_6M`. Der Fokus bleibt katalogfrei: Die allgemeinen `ColorPatch`- und `RectBorder`-Opacity-Probes erhalten eine 8388608th-yoctofeine Zwischenstufe direkt um die bisherige BackBottom-Zielopacity.

## Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt bei `ColorPatch.fill_opacity` und `RectBorder.fill_opacity` zusätzlich `0.98281249999417923390865325927734375`.
- Für `ColorPatch.stroke_opacity` und `RectBorder.stroke_opacity` wird spiegelbildlich `0.98281250000582076609134674072265625` geprüft.
- Neue Helper-Tests sichern, dass der reguläre Optimiererpfad die neuen 8388608th-yoctofeinen Zwischenstufen nur bei sinkendem Fehler akzeptiert.
- Die Änderung hängt weder an `GE9012_6M` noch an einer anderen Runtime-Bild-ID.

## Plan-B-/Perception-Lerneffekt

`GE9012_6M` bleibt ein beschreibungsbasierter BackBottom-/Rechteck-Contract. Run AAA erweitert nicht die reine Bilddetektion, sondern den allgemeinen Opacity-Registrierungsraum für vorhandene Rechteckflächen und -konturen. Der Perception-Lerneffekt bleibt auf Seed-Ebene `nur Sonderfall`; die nachgelagerte Opacity-Feinregistrierung ist katalogfrei generalisiert.

## Validierung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_color_patch_opacity_with_8388608th_yoctofine_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rect_border_stroke_opacity_with_8388608th_yoctofine_probe` läuft grün mit `2 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün mit `0 occurrences`.

## Ergebnis / nächster Schritt

Run AAA schließt den dokumentierten GE9012_6M-Feinschritt auf Code- und Helper-Test-Ebene ab. Rechteckige Füll- und Konturelemente können nun eine zusätzliche 8388608th-yoctofeine Opacity-Zwischenregistrierung nutzen. Das nächste Arbeitspaket kann in der aktiven Plan-B-Rotation zu `GE9013_1M` wechseln oder weiteres allgemeines Rechteck-/Opacity-Feintuning prüfen.
