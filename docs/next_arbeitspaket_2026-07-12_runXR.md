# Nächstes Arbeitspaket – GE9013_1M Eighth-Yoctofine-Warmfill-Probe Run XR (2026-07-12)

Run XR arbeitet nach `docs/next_arbeitspaket_2026-07-12_runXQ.md` den nächsten Schritt in der aktiven Plan-B-Rotation ab und kehrt zu `GE9013_1M` zurück. Der Fokus bleibt katalogfrei: Die allgemeine `ColorPatch`-/`RectBorder`-Farbregistrierung erhält eine weitere eighth-yoctofeine warme Zwischenfarbe für BackBottom-ähnliche helle Rechteckfüllungen.

## Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt bei rechteckigen `ColorPatch`- und `RectBorder`-Füllflächen zusätzlich `#f3baba` als eighth-yoctofeine warme Zwischenfarbe nach den bestehenden BackBottom-Farbankern.
- Ein neuer Helper-Test sichert, dass diese Probe ausschließlich über den regulären Optimiererpfad und nur bei sinkendem Fehler akzeptiert wird.
- Die Änderung hängt weder an `GE9013_1M` noch an eine andere Runtime-Bild-ID.

## Plan-B-/Perception-Lerneffekt

`GE9013_1M` bleibt ein beschreibungsbasierter BackBottom-/hellgraues-Quadrat-Contract mit rechteckiger Füllfläche und Kontur. Run XR erweitert nicht die reine Bilddetektion, sondern den allgemeinen Registrierungsraum für vorhandene rechteckige Füllelemente. Der Perception-Lerneffekt bleibt auf Ebene der Seed-Quelle `nur Sonderfall`, die nachgelagerte Warmfill-Registrierung ist aber katalogfrei generalisiert.

## Validierung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rect_to_eighth_yoctofine_warm_light_fill` läuft grün mit `1 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün mit `0 occurrences`.

## Ergebnis / nächster Schritt

Run XR schließt den dokumentierten GE9013_1M-Feinschritt auf Code- und Testebene ab. Rechteckige Füllflächen können nun eine zusätzliche eighth-yoctofeine warme Zwischenfarbe nutzen. Das nächste Arbeitspaket kann in der aktiven Plan-B-Rotation wieder zu `DLG0021` wechseln oder weiteres allgemeines BackBottom-/Rechteck-Feintuning prüfen.
