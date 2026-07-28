# Nächstes Arbeitspaket – GE9012_6M 33554432nd-Yoctofine-Opacity-Probes Run AAF (2026-07-28)

Run AAF arbeitet nach `docs/next_arbeitspaket_2026-07-28_runAAE.md` den nächsten Schritt in der aktiven Plan-B-Rotation ab und wechselt zu `GE9012_6M`. Der Fokus bleibt katalogfrei: Die allgemeinen `ColorPatch`- und `RectBorder`-Opacity-Probes erhalten eine 33554432nd-yoctofeine Zwischenstufe direkt um die bisherige BackBottom-Zielopacity.

## Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt bei `ColorPatch.fill_opacity` und `RectBorder.fill_opacity` zusätzlich `0.9828124999985448084771633148193359375`.
- Für `ColorPatch.stroke_opacity` und `RectBorder.stroke_opacity` wird spiegelbildlich `0.9828125000014551915228366851806640625` geprüft.
- Neue Helper-Tests sichern, dass der reguläre Optimiererpfad die neuen Zwischenstufen nur bei sinkendem Fehler akzeptiert.
- Die Änderung hängt weder an `GE9012_6M` noch an einer anderen Runtime-Bild-ID.

## Plan-B-/Perception-Lerneffekt

`GE9012_6M` bleibt ein beschreibungsbasierter BackBottom-/Rechteck-Contract. Run AAF erweitert nicht die reine Bilddetektion, sondern den allgemeinen Opacity-Registrierungsraum für vorhandene Rechteckflächen und -konturen. Der Perception-Lerneffekt bleibt auf Seed-Ebene `nur Sonderfall`; die nachgelagerte Opacity-Feinregistrierung ist katalogfrei generalisiert.

## Validierung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_color_patch_opacity_with_33554432nd_yoctofine_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rect_border_stroke_opacity_with_33554432nd_yoctofine_probe` läuft grün mit `2 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün mit `0 occurrences`.

## Ergebnis / nächster Schritt

Run AAF schließt den dokumentierten GE9012_6M-Feinschritt auf Code- und Helper-Test-Ebene ab. Rechteckige Füll- und Konturelemente können nun eine zusätzliche 33554432nd-yoctofeine Opacity-Zwischenregistrierung nutzen. Das nächste Arbeitspaket kann in der aktiven Plan-B-Rotation zu `GE9013_1M` wechseln oder weiteres allgemeines Rechteck-/Opacity-Feintuning prüfen.
