# Nächstes Arbeitspaket – GE9012_6M 536870912th-Yoctofine-Opacity-Probes Run AAP (2026-07-29)

Run AAP arbeitet nach `docs/next_arbeitspaket_2026-07-29_runAAO.md` den nächsten Schritt in der aktiven Plan-B-Rotation ab und wechselt zu `GE9012_6M`. Der Fokus bleibt katalogfrei: Die allgemeinen `ColorPatch`- und `RectBorder`-Opacity-Probes erhalten eine 536870912th-yoctofeine Zwischenstufe direkt um die bisherige BackBottom-Zielopacity.

## Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt bei `ColorPatch.fill_opacity` und `RectBorder.fill_opacity` zusätzlich `0.98281249999990905052982270717620849609375`.
- Für `ColorPatch.stroke_opacity` und `RectBorder.stroke_opacity` wird spiegelbildlich `0.98281250000009094947017729282379150390625` geprüft.
- Neue Helper-Tests sichern, dass der reguläre Optimiererpfad die neuen Zwischenstufen nur bei sinkendem Fehler akzeptiert.
- Die Änderung hängt weder an `GE9012_6M` noch an einer anderen Runtime-Bild-ID.

## Plan-B-/Perception-Lerneffekt

`GE9012_6M` bleibt ein beschreibungsbasierter BackBottom-/Rechteck-Contract. Run AAP erweitert nicht die reine Bilddetektion, sondern den allgemeinen Opacity-Registrierungsraum für vorhandene Rechteckflächen und -konturen. Der Perception-Lerneffekt bleibt auf Seed-Ebene `nur Sonderfall`; die nachgelagerte Opacity-Feinregistrierung ist katalogfrei generalisiert.

## Validierung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_color_patch_opacity_with_536870912th_yoctofine_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rect_border_stroke_opacity_with_536870912th_yoctofine_probe` läuft grün mit `2 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün mit `0 occurrences`.

## Ergebnis / nächster Schritt

Run AAP schließt den dokumentierten GE9012_6M-Feinschritt auf Code- und Helper-Test-Ebene ab. Rechteckige Füll- und Konturelemente können nun eine zusätzliche 536870912th-yoctofeine Opacity-Zwischenregistrierung nutzen. Das nächste Arbeitspaket kann in der aktiven Plan-B-Rotation zu `GE9013_1M` wechseln oder weiteres allgemeines Rechteck-/Opacity-Feintuning prüfen.
