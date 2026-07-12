# Nächstes Arbeitspaket – DLG0021 Sixteenth-Yoctofine-Gradient-Offset Run XN (2026-07-12)

Run XN rotiert nach `docs/next_arbeitspaket_2026-07-12_runXM.md` in der aktiven Plan-B-Kandidatenliste wieder zu `DLG0021`. Der Fokus bleibt katalogfrei: Die allgemeinen `PolygonPath`-Stroke-Gradient-Offset-Probes erhalten eine sixteenth-yoctofeine Zwischenstufe für antialiasing-empfindliche Hakenkonturen.

## Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt bei `PolygonPath`-Elementen mit `stroke_gradient` zusätzlich `±0.0000030517578125` als Offset-Delta.
- Ein neuer Helper-Test sichert, dass ein `50.00030517578125%`-Zwischenstopp ausschließlich über den regulären Optimiererpfad auf `50%` zurückregistriert und nur bei sinkendem Fehler akzeptiert wird.
- Die Änderung hängt weder an `DLG0021` noch an eine andere Runtime-Bild-ID.

## Plan-B-/Perception-Lerneffekt

`DLG0021` bleibt ein beschreibungsbasierter Checkbox-/Haken-Contract mit manueller Seed-Annahme. Run XN erweitert nicht die reine Bilddetektion, sondern den allgemeinen Registrierungsraum für vorhandene `PolygonPath`-Stroke-Gradienten. Der Perception-Lerneffekt bleibt auf Ebene der Seed-Quelle `nur Sonderfall`; die nachgelagerte Gradient-Offset-Registrierung ist weiterhin katalogfrei generalisiert.

## Validierung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_stroke_gradient_offsets_with_sixteenth_yoctofine_probe` läuft grün mit `1 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. ICC_MAX_QUALITY_PASSES=1 timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-dlg0021-runXN --start DLG0021 --end DLG0021 --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; der isolierte DLG0021-Einzellauf endet bei `Mean-Delta²=16476.853516` und `Fehler/Pixel=0.075292` im ersten Qualitätsdurchlauf.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün mit `0 occurrences`.

## Ergebnis

Run XN schließt den dokumentierten DLG0021-Feinschritt auf Code-, Test- und isolierter Recheck-Ebene ab. Polygonpfad-Stroke-Gradienten können nun eine sixteenth-yoctofeine Offset-Zwischenregistrierung nutzen; der isolierte DLG0021-Recheck sinkt gegenüber Run XI von `Mean-Delta²=16622.357422` auf `Mean-Delta²=16476.853516`. Das nächste Arbeitspaket kann in der aktiven Plan-B-Rotation zu `GE1410_L` wechseln oder weiteres allgemeines PolygonPath-/Gradient-Antialiasing-Feintuning prüfen.
