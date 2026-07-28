# Nächstes Arbeitspaket – DLG0021 65536th-Yoctofine-Gradient-Offset-Probes Run AAC (2026-07-28)

Run AAC arbeitet nach `docs/next_arbeitspaket_2026-07-27_runAAB.md` den nächsten Schritt in der aktiven Plan-B-Rotation ab und kehrt zu `DLG0021` zurück. Der Fokus bleibt katalogfrei: Die allgemeinen `PolygonPath`-Stroke-Gradient-Offset-Probes erhalten eine 65536th-yoctofeine Zwischenstufe um die bisherige Checkbox-/Haken-Gradientenregistrierung.

## Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt bei `PolygonPath.stroke_gradient.stops[].offset` zusätzlich `±0.0000000007450580596923828125` als 65536th-yoctofeine Zwischenregistrierung.
- Die Mindestdistanz für eigenständige Offset-Kandidaten sinkt passend von `1e-9` auf `1e-12`, damit die neue Stufe nicht als numerisch identisch verworfen wird.
- Ein neuer Helper-Test sichert, dass ein Offset von `50.00000007450580596923828125%` über den regulären Optimiererpfad auf `50%` zurückregistriert und nur bei sinkendem Fehler akzeptiert wird.
- Die Änderung hängt weder an `DLG0021` noch an einer anderen Runtime-Bild-ID.

## Plan-B-/Perception-Lerneffekt

`DLG0021` bleibt ein beschreibungsbasierter Checkbox-/Haken-Contract. Run AAC erweitert nicht die reine Bilddetektion, sondern den allgemeinen Registrierungsraum für vorhandene `PolygonPath`-Stroke-Gradienten. Der Perception-Lerneffekt bleibt auf Seed-Ebene `nur Sonderfall`; die nachgelagerte Gradienten-Feinregistrierung ist katalogfrei generalisiert.

## Validierung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_stroke_gradient_offsets_with_65536th_yoctofine_probe` läuft grün mit `1 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün mit `0 occurrences`.

## Ergebnis / nächster Schritt

Run AAC schließt den dokumentierten DLG0021-Feinschritt auf Code- und Helper-Test-Ebene ab. Polygonpfad-Stroke-Gradienten können nun eine zusätzliche 65536th-yoctofeine Offset-Zwischenregistrierung nutzen. Das nächste Arbeitspaket kann in der aktiven Plan-B-Rotation zu `GE1410_L` wechseln oder weiteres allgemeines PolygonPath-Antialiasing-/Kontur-Feintuning prüfen.
