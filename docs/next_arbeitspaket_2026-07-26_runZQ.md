# Nächstes Arbeitspaket – GE9012_6M 524288th-Yoctofine-Opacity-Probes Run ZQ (2026-07-26)

Run ZQ arbeitet nach `docs/next_arbeitspaket_2026-07-26_runZP.md` den nächsten Schritt in der aktiven Plan-B-Rotation ab und wechselt zu `GE9012_6M`. Der Fokus bleibt katalogfrei: Die allgemeinen `ColorPatch`- und `RectBorder`-Opacity-Probes erhalten eine 524288th-yoctofeine Zwischenstufe direkt um die bisherige BackBottom-Zielopacity.

## Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt bei `ColorPatch.fill_opacity` zusätzlich `0.9828124999068677425384521484375` als 524288th-yoctofeine Zwischenstufe unterhalb von `0.9828125`.
- Die allgemeine Geometry-IR-Optimierung probt bei `RectBorder.stroke_opacity` zusätzlich `0.9828125000931322574615478515625` als 524288th-yoctofeine Zwischenstufe oberhalb von `0.9828125`.
- Zwei neue Helper-Tests sichern, dass die neuen Opacity-Probes nur über den regulären Optimiererpfad und nur bei sinkendem Fehler akzeptiert werden.
- Die Änderung hängt weder an `GE9012_6M` noch an einer anderen Runtime-Bild-ID.

## Plan-B-/Perception-Lerneffekt

`GE9012_6M` bleibt ein beschreibungsbasierter BackBottom-/Light-Grey-Square-Contract. Run ZQ erweitert nicht die reine Bilddetektion, sondern den allgemeinen Registrierungsraum für vorhandene rechteckige Füll- und Konturelemente. Der Perception-Lerneffekt bleibt auf Ebene der Seed-Quelle `nur Sonderfall`, die nachgelagerte Opacity-Registrierung ist aber katalogfrei generalisiert.

## Validierung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_color_patch_opacity_with_524288th_yoctofine_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rect_border_stroke_opacity_with_524288th_yoctofine_probe` läuft grün mit `2 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün mit `0 occurrences`.

## Ergebnis / nächster Schritt

Run ZQ schließt den dokumentierten GE9012_6M-Feinschritt auf Code- und Helper-Test-Ebene ab. Rechteckige Füll- und Konturelemente können nun eine zusätzliche 524288th-yoctofeine Opacity-Zwischenregistrierung nutzen. Das nächste Arbeitspaket kann in der aktiven Plan-B-Rotation zu `GE9013_1M` wechseln oder weiteres allgemeines Rechteck-/Opacity-Feintuning prüfen.
