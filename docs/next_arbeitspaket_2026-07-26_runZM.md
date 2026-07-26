# Nächstes Arbeitspaket – GE9013_1M 262144th-Yoctofine-Opacity-Probes Run ZM (2026-07-26)

Run ZM arbeitet nach `docs/next_arbeitspaket_2026-07-26_runZL.md` den nächsten Schritt in der aktiven Plan-B-Rotation ab und wechselt zu `GE9013_1M`. Der Fokus bleibt katalogfrei: Die allgemeinen `ColorPatch`- und `RectBorder`-Opacity-Probes erhalten eine 262144th-yoctofeine Zwischenstufe direkt um die bisherige BackBottom-Zielopacity.

## Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt bei `ColorPatch.fill_opacity` zusätzlich `0.982812499813735485076904296875` als 262144th-yoctofeine Zwischenstufe unterhalb von `0.9828125`.
- Die allgemeine Geometry-IR-Optimierung probt bei `RectBorder.stroke_opacity` zusätzlich `0.982812500186264514923095703125` als 262144th-yoctofeine Zwischenstufe oberhalb von `0.9828125`.
- Zwei neue Helper-Tests sichern, dass die neuen Opacity-Probes nur über den regulären Optimiererpfad und nur bei sinkendem Fehler akzeptiert werden.
- Die Änderung hängt weder an `GE9013_1M` noch an eine andere Runtime-Bild-ID.
- Die GitHub-Actions-Pipeline führt auf Pull Requests und Branch-Pushes jetzt auch Safe-Baseline, Regressionstests, die vollständige Heavy-Suite und die vollständige Katalogkonvertierung aus; damit werden alle zehn statt nur sechs Job-Ausführungen angefordert.

## Plan-B-/Perception-Lerneffekt

`GE9013_1M` bleibt ein beschreibungsbasierter BackBottom-/Light-Grey-Square-Contract. Run ZM erweitert nicht die reine Bilddetektion, sondern den allgemeinen Registrierungsraum für vorhandene rechteckige Füll- und Konturelemente. Der Perception-Lerneffekt bleibt auf Ebene der Seed-Quelle `nur Sonderfall`, die nachgelagerte Opacity-Registrierung ist aber katalogfrei generalisiert.

## Validierung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_color_patch_opacity_with_262144th_yoctofine_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rect_border_stroke_opacity_with_262144th_yoctofine_probe` läuft grün mit `2 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün mit `0 occurrences`.

## Ergebnis / nächster Schritt

Run ZM schließt den dokumentierten GE9013_1M-Feinschritt auf Code- und Helper-Test-Ebene ab. Rechteckige Füll- und Konturelemente können nun eine zusätzliche 262144th-yoctofeine Opacity-Zwischenregistrierung nutzen. In `docs/open_tasks.md` verbleiben nach der dokumentierten Checkbox-Zählregel 27 offene Aufgaben; die aktive Plan-B-Rotation enthält weiterhin fünf Kandidaten. Das nächste Arbeitspaket kann zu `DLG0021` wechseln oder weiteres allgemeines Gradienten-/Opacity-Feintuning prüfen.
