# Nächstes Arbeitspaket – GE1410_L Sixteenth-Yoctofine-PolygonPath-Probes Run XO (2026-07-12)

Run XO leitet sich aus dem hochgeladenen Volltest-/Arbeitsstand nach `docs/next_arbeitspaket_2026-07-12_runXN.md` ab und rotiert in der aktiven Plan-B-Kandidatenliste zu `GE1410_L`. Der Fokus bleibt katalogfrei: Die allgemeinen `PolygonPath`-Punkt- und Stroke-Width-Probes erhalten eine sixteenth-yoctofeine Zwischenstufe für antialiasing-empfindliche Dreiecks- und Diagrammkonturen.

## Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt bei `PolygonPath`-Stroke-Widths zusätzlich `±0.000001220703125` als absolutes Delta.
- Die allgemeine Geometry-IR-Optimierung probt bei einzelnen `PolygonPath`-Punktkoordinaten ebenfalls zusätzlich `±0.000001220703125` als Subpixel-Delta.
- Zwei neue Helper-Tests sichern, dass beide Zwischenstufen ausschließlich über den regulären Optimiererpfad und nur bei sinkendem Fehler akzeptiert werden.
- Die Änderung hängt weder an `GE1410_L` noch an eine andere Runtime-Bild-ID.

## Plan-B-/Perception-Lerneffekt

`GE1410_L` bleibt ein beschreibungsbasierter Diagramm-/Achsen-/Dreieck-Contract, dessen Primitive bereits als PolygonPath-/Linien-Seeds generalisiert sind. Run XO erweitert nicht die reine Bilddetektion, sondern den allgemeinen Registrierungsraum für vorhandene `PolygonPath`-Geometrie und Konturstärken. Der Perception-Lerneffekt bleibt daher `generalisiert`.

## Validierung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_points_with_sixteenth_yoctofine_subpixel_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_stroke_width_with_sixteenth_yoctofine_absolute_probe` läuft grün mit `2 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. ICC_MAX_QUALITY_PASSES=1 timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ge1410-runXO --start GE1410_L --end GE1410_L --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; der isolierte `GE1410_L`-Einzellauf endet im besten Qualitätsdurchlauf bei `Mean-Delta²=584.927979` und `Fehler/Pixel=0.009801`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün mit `0 occurrences`.

## Ergebnis / nächster Schritt

Run XO schließt den abgeleiteten GE1410_L-Feinschritt auf Code-, Test- und isolierter Recheck-Ebene ab. Polygonpfade können nun sixteenth-yoctofeine Punkt- und Konturstärken-Zwischenregistrierung nutzen. Das nächste Arbeitspaket kann in der aktiven Plan-B-Rotation zu `SE0041_1` wechseln oder weiteres allgemeines Antialiasing-/Stem-Feintuning prüfen.
