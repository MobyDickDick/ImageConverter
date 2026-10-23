# Nächstes Arbeitspaket – DLG0021 Quarter-Yoctofine-Gradient-Probes Run XD (2026-07-10)

Run XD arbeitet den nach Run XC dokumentierten Anschluss im aktiven
Plan-B-Kandidaten `DLG0021` ab. Der Fokus bleibt katalogfrei: Die allgemeinen
`PolygonPath`-Stroke-Gradient-Offset-Probes werden um eine quarter-yoctofeine
Zwischenstufe ergänzt.

## Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt bei `PolygonPath`-
  `stroke_gradient.stops[*].offset` zusätzlich `±0.001220703125` Prozentpunkte
  im Offset-Raum.
- Ein neuer Helper-Test sichert, dass ein Stop bei `50.001220703125%` durch die
  zusätzliche Probe auf `50%` registriert und nur bei sinkendem Fehler akzeptiert
  wird.
- Die Änderung hängt weder an `DLG0021` noch an eine andere Runtime-Bild-ID.

## Plan-B-/Perception-Lerneffekt

`DLG0021` bleibt ein beschreibungsbasierter Checkbox-/Haken-Contract mit
`PolygonPath`-Kontur und grün-grauem Stroke-Gradienten. Run XD erweitert nicht
die reine Bilddetektion, sondern den allgemeinen Optimierungsraum für bereits
vorhandene `PolygonPath`-Gradientenkonturen. Der Perception-Lerneffekt bleibt
`nur Sonderfall` auf Ebene der Seed-Quelle, aber die nachgelagerte Registrierung
ist katalogfrei generalisiert.

## Validierung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_stroke_gradient_offsets_with_quarter_yoctofine_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_stroke_gradient_offsets_with_half_yoctofine_probe` läuft grün mit `2 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. ICC_MAX_QUALITY_PASSES=1 timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-dlg0021-runXD --start DLG0021 --end DLG0021 --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; der isolierte DLG0021-Einzellauf verbessert sich auf `Mean-Delta²=16540.876953` und `Fehler/Pixel=0.075956`.

## Ergebnis

Run XD schließt den dokumentierten DLG0021-Feinschritt ab. Die zusätzliche
quarter-yoctofeine Offset-Probe ist als allgemeiner Optimiererpfad abgesichert
und senkt im isolierten DLG0021-Recheck den Restfehler gegenüber Run XC. Das
nächste Arbeitspaket kann in der aktiven Plan-B-Rotation zu `GE1410_L` wechseln
oder weitere allgemeine PolygonPath-/Gradient-Feinregistrierung prüfen.
