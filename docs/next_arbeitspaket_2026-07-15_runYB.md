# Nächstes Arbeitspaket – GE9013_1M Thirtysecond-Yoctofine-Warm-Fill-Probe Run YB (2026-07-15)

Run YB arbeitet nach `docs/next_arbeitspaket_2026-07-15_runYA.md` den nächsten Schritt in der aktiven Plan-B-Rotation ab und wechselt zu `GE9013_1M`. Der Fokus bleibt katalogfrei: Die allgemeine `ColorPatch`-/`RectBorder`-Farbregistrierung erhält eine weitere warme Zwischenfarbe für antialiasing-empfindliche BackBottom-ähnliche Füllflächen.

## Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt bei `ColorPatch`-/`RectBorder`-`fill` zusätzlich `#f3babc` als thirtysecond-yoctofeine warme Zwischenfarbe nach `#f3babb`.
- Ein neuer Helper-Test sichert ab, dass die Zwischenfarbe nur über den regulären Optimiererpfad und nur bei sinkendem Fehler akzeptiert wird.
- Die Änderung hängt weder an `GE9013_1M` noch an eine andere Runtime-Bild-ID.

## Plan-B-/Perception-Lerneffekt

`GE9013_1M` bleibt ein beschreibungsbasierter BackBottom-/helles-Rechteck-Contract mit warmer Füllregistrierung. Run YB erweitert nicht die reine Bilddetektion, sondern den allgemeinen Registrierungsraum vorhandener rechteckiger Füllflächen. Der Perception-Lerneffekt bleibt damit `generalisiert` für den nachgelagerten Optimiererpfad.

## Validierung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rect_to_thirtysecond_yoctofine_warm_light_fill` läuft grün mit `1 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün mit `0 occurrences`.

## Ergebnis / nächster Schritt

Run YB schließt den dokumentierten GE9013_1M-Feinschritt auf Code- und Testebene ab. Warme BackBottom-ähnliche Rechteckfüllungen können nun eine thirtysecond-yoctofeine Zwischenregistrierung nutzen. Das nächste Arbeitspaket kann in der aktiven Plan-B-Rotation zu `DLG0021` wechseln oder weiteres allgemeines warmes Füllfarb-Feintuning prüfen.
