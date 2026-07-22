# Nächstes Arbeitspaket – DLG0021 PolygonPath-Quarter-Midpoint-Opacity-Probes Run YY (2026-07-21)

Run YY arbeitet nach `docs/next_arbeitspaket_2026-07-21_runYX.md` den nächsten Schritt in der aktiven Plan-B-Rotation ab und wechselt erneut zu `DLG0021`. Der Fokus bleibt katalogfrei: Die allgemeinen `PolygonPath`-Opacity-Probes erhalten weitere Viertel-Zwischenwerte zwischen den bereits vorhandenen mittleren Stufen.

## Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt bei `PolygonPath.stroke_opacity` zusätzlich `0.8875`, `0.9125`, `0.9375` und `0.9625` zwischen den bestehenden Opacity-Stufen.
- Die allgemeine Geometry-IR-Optimierung probt bei `PolygonPath.fill_opacity` dieselben Viertel-Zwischenwerte, damit gefüllte Pfade und Konturpfade denselben katalogfreien Registrierungsraum nutzen.
- Zwei neue Helper-Tests sichern, dass die neuen Viertel-Zwischenwerte ausschließlich über den regulären Optimiererpfad und nur bei sinkendem Fehler akzeptiert werden.
- Die Änderung hängt weder an `DLG0021` noch an eine andere Runtime-Bild-ID.

## Plan-B-/Perception-Lerneffekt

`DLG0021` bleibt ein beschreibungsbasierter Checkbox-/Checkmark-Contract. Run YY erweitert nicht die reine Bilddetektion, sondern den allgemeinen Registrierungsraum für vorhandene `PolygonPath`-Füllungen und -Konturen. Der Perception-Lerneffekt bleibt auf Ebene der Seed-Quelle `nur Sonderfall`, die nachgelagerte Opacity-Registrierung ist aber katalogfrei generalisiert.

## Validierung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_stroke_opacity_with_quarter_midpoint_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_fill_opacity_with_quarter_midpoint_probe` läuft grün mit `2 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün mit `0 occurrences`.

## Ergebnis / nächster Schritt

Run YY schließt den dokumentierten DLG0021-Feinschritt auf Code- und Helper-Test-Ebene ab. Polygonpfade können nun zusätzliche Viertel-Zwischenregistrierungen für Opacity nutzen. Das nächste Arbeitspaket kann in der aktiven Plan-B-Rotation zu `GE1410_L` wechseln oder weiteres allgemeines PolygonPath-Antialiasing-/Kontur-Feintuning prüfen.
