# Nächstes Arbeitspaket – DLG0021 Yoctofine-Gradient-Offset-Probes Run VX (2026-07-08)

Run VX setzt den in Run VW dokumentierten allgemeinen Gradient-/PolygonPath-Feinschnitt fort. Der Fokus bleibt katalogfrei: Die bereits allgemeinen `PolygonPath.stroke_gradient.stops[*].offset`-Probes werden um eine noch feinere yoctofeine Stufe ergänzt.

## 1) Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt für vorhandene `stroke_gradient.stops` zusätzlich yoctofeine Offset-Deltas von `±0.000048828125` relativ zum aktuellen Stop-Offset.
- Die neue Stufe liegt zwischen dem zeptofeinen Schritt `±0.00009765625` und dem unveränderten Ausgangswert und wird wie alle Elementprobes nur übernommen, wenn der gerenderte Fehler im Elementschritt strikt sinkt.
- Die Änderung ist deterministisch und katalogfrei; sie koppelt weder an `DLG0021` noch an eine andere Runtime-Bild-ID.

## 2) Perception-Lerneffekt

`DLG0021` bleibt auf Ebene des initialen Checkbox-/Haken-Contracts ein `nur Sonderfall`-Signal. Run VX erweitert nicht die Bilddetektion, sondern den allgemeinen Optimierungsraum für bereits vorhandene `PolygonPath`-Konturen mit Stroke-Gradienten, die aus neutralen Pfad- und Farbverlaufsbeschreibungen entstehen.

## 3) Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_stroke_gradient_offsets_with_yoctofine_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_stroke_gradient_offsets_with_zeptofine_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_stroke_gradient_offsets_with_attofine_probe` läuft grün mit `3 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün und bestätigt weiterhin `0` Runtime-ID-Vorkommen.

## 4) Ergebnis / nächster Schritt

Run VX schließt den dokumentierten DLG0021-Folge-Feinschritt ab. `PolygonPath`-Stroke-Gradient-Offsets können nun katalogfrei yoctofeine Nachbarwerte bewerten. Das nächste Arbeitspaket kann in der aktiven Plan-B-Rotation zu `GE1410_L` wechseln oder weiteres allgemeines Antialiasing-/Gradient-Tuning prüfen.
