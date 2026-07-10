# Nächstes Arbeitspaket – GE1410_L Half-Yoctofine-PolygonPath-Probes Run XE (2026-07-10)

Run XE rotiert nach `docs/next_arbeitspaket_2026-07-10_runXD.md` in der
aktiven Plan-B-Kandidatenliste zu `GE1410_L`. Der Fokus bleibt katalogfrei:
Die allgemeinen `PolygonPath`-Punkt- und `stroke_width`-Probes werden um eine
half-yoctofeine Zwischenstufe ergänzt.

## Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt bei `PolygonPath`-Punkten
  zusätzlich `±0.0000048828125` im normierten Koordinatenraum.
- Dieselbe half-yoctofeine absolute Zwischenstufe wird für `PolygonPath`-
  `stroke_width` ergänzt.
- Zwei neue Helper-Tests sichern, dass die neuen Probes nur über den regulären
  Optimiererpfad und nur bei sinkendem Fehler akzeptiert werden.
- Die Änderung hängt weder an `GE1410_L` noch an eine andere Runtime-Bild-ID.

## Plan-B-/Perception-Lerneffekt

`GE1410_L` bleibt ein katalogfrei generalisierter Diagramm-/Dreieck-Contract:
Achsen-/Linien- und Dreiecksprimitive liegen als `PolygonPath`-Elemente vor.
Run XE erweitert nicht die reine Bilddetektion, sondern den allgemeinen
Registrierungsraum für vorhandene Polygonpfade. Der Perception-Lerneffekt bleibt
`generalisiert`.

## Validierung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_points_with_half_yoctofine_subpixel_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_stroke_width_with_half_yoctofine_absolute_probe` läuft grün mit `2 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. ICC_MAX_QUALITY_PASSES=1 timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ge1410-runXE --start GE1410_L --end GE1410_L --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; der isolierte GE1410_L-Einzellauf meldet `Mean-Delta²=538.665588` und `Fehler/Pixel=0.008912`.

## Ergebnis

Run XE schließt den dokumentierten GE1410_L-Feinschritt ab. Polygonpfade können
nun eine half-yoctofeine lokale Punkt- und absolute Stroke-Width-Registrierung
nutzen; der isolierte GE1410_L-Einzellauf bleibt grün und liegt unter den zuvor
dokumentierten Plan-B-Restfehlern. Das nächste Arbeitspaket kann in der aktiven
Plan-B-Rotation zu `SE0041_1` wechseln oder weitere allgemeine
Antialiasing-/PolygonPath-Feinregistrierung prüfen.
