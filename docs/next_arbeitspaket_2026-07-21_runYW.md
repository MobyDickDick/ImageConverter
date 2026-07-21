# Nächstes Arbeitspaket – GE1410_L PolygonPath-High-Midpoint-Opacity-Probes Run YW (2026-07-21)

Run YW rotiert nach `docs/next_arbeitspaket_2026-07-21_runYV.md` zum
Plan-B-Kandidaten `GE1410_L`. Der Fokus bleibt katalogfrei: Die allgemeinen
`PolygonPath`-Opacity-Probes erhalten einen zusätzlichen Zwischenwert zwischen
`0.95` und `1.0`, damit beschreibungsbasierte Pfadkonturen und gefüllte Pfade
nicht nur auf die groben oberen Opacity-Stufen registrieren können.

## Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt bei `PolygonPath.stroke_opacity`
  zusätzlich `0.975` zwischen den bestehenden oberen Opacity-Stufen.
- Die allgemeine Geometry-IR-Optimierung probt bei `PolygonPath.fill_opacity`
  denselben Zwischenwert, damit gefüllte Pfade den gleichen katalogfreien
  Registrierungsraum nutzen.
- Zwei neue Helper-Tests sichern, dass der neue Zwischenwert ausschließlich über
  den regulären Optimiererpfad und nur bei sinkendem Fehler akzeptiert wird.
- Die Änderung hängt weder an `GE1410_L` noch an eine andere Runtime-Bild-ID.

## Plan-B-/Perception-Lerneffekt

`GE1410_L` bleibt ein beschreibungsbasierter Pfad-/Kontur-Contract. Run YW
erweitert nicht die reine Bilddetektion, sondern den allgemeinen
Registrierungsraum für vorhandene `PolygonPath`-Füllungen und -Konturen. Der
Perception-Lerneffekt bleibt auf Ebene der Seed-Quelle `nur Sonderfall`, die
nachgelagerte Opacity-Registrierung ist aber katalogfrei generalisiert.

## Validierung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_stroke_opacity_with_high_midpoint_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_fill_opacity_with_high_midpoint_probe` läuft grün mit `2 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün mit `0 occurrences`.

## Ergebnis / nächster Schritt

Run YW schließt den dokumentierten GE1410_L-Feinschritt auf Code- und
Helper-Test-Ebene ab. Polygonpfade können nun zusätzliche obere Opacity-
Zwischenregistrierungen nutzen. Das nächste Arbeitspaket kann in der aktiven
Plan-B-Rotation zu `GE9013_1M` wechseln oder weiteres allgemeines
PolygonPath-Antialiasing-/Kontur-Feintuning prüfen.
