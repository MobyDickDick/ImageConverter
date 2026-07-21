# Nächstes Arbeitspaket – GE9013_1M Sixtyfourth-Yoctofine-Warmfill-Probe Run YX (2026-07-21)

Run YX arbeitet nach `docs/next_arbeitspaket_2026-07-21_runYW.md` den nächsten Schritt in der aktiven Plan-B-Rotation ab und wechselt zu `GE9013_1M`. Der Fokus bleibt katalogfrei: Die allgemeine `ColorPatch`-/`RectBorder`-Farbregistrierung erhält eine weitere sixtyfourth-yoctofeine warme Zwischenfarbe für BackBottom-ähnliche helle Rechteckfüllungen.

## Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt bei `ColorPatch` und `RectBorder` zusätzlich die warme Füllfarbe `#f3babd` neben den bereits vorhandenen BackBottom-ähnlichen Warmfüllungen.
- Ein neuer Helper-Test sichert, dass der reguläre Optimiererpfad die neue warme Zwischenfarbe nur bei sinkendem Fehler akzeptiert.
- Die Änderung hängt weder an `GE9013_1M` noch an eine andere Runtime-Bild-ID.

## Plan-B-/Perception-Lerneffekt

`GE9013_1M` bleibt ein beschreibungsbasierter BackBottom-/Light-Grey-Square-Contract. Run YX erweitert nicht die reine Bilddetektion, sondern den allgemeinen Registrierungsraum für vorhandene rechteckige Füllflächen. Der Perception-Lerneffekt bleibt auf Ebene der Seed-Quelle `nur Sonderfall`, die nachgelagerte Warmfüllungs-Registrierung ist aber katalogfrei generalisiert.

## Validierung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rect_to_sixtyfourth_yoctofine_warm_light_fill` läuft grün mit `1 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün mit `0 occurrences`.

## Ergebnis / nächster Schritt

Run YX schließt den dokumentierten GE9013_1M-Feinschritt auf Code- und Helper-Test-Ebene ab. BackBottom-ähnliche rechteckige Füllflächen können nun eine weitere sixtyfourth-yoctofeine warme Zwischenfarbe nutzen. Das nächste Arbeitspaket kann in der aktiven Plan-B-Rotation zu `DLG0021` wechseln oder weiteres allgemeines Rechteck-/Füllfarben-Feintuning prüfen.
