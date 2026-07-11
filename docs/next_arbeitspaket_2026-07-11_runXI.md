# Nächstes Arbeitspaket – DLG0021 Eighth-Yoctofine-Gradient-Offset Run XI (2026-07-11)

Run XI rotiert nach `docs/next_arbeitspaket_2026-07-11_runXH.md` in der
aktiven Plan-B-Kandidatenliste wieder zu `DLG0021`. Der Fokus bleibt
katalogfrei: Die allgemeinen `PolygonPath`-`stroke_gradient`-Offset-Probes
werden um eine eighth-yoctofeine Zwischenstufe ergänzt.

## Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt bei `PolygonPath`-
  `stroke_gradient`-Stop-Offsets zusätzlich `±0.000006103515625` im normierten
  Offset-Raum, entsprechend `±0.0006103515625` Prozentpunkten.
- Ein neuer Helper-Test sichert, dass diese Probe ausschließlich über den
  regulären Optimiererpfad und nur bei sinkendem Fehler akzeptiert wird.
- Die Änderung hängt weder an `DLG0021` noch an eine andere Runtime-Bild-ID.

## Plan-B-/Perception-Lerneffekt

`DLG0021` bleibt ein neutraler Checkbox-/Haken-Primitive-Contract mit
manueller Seed-Annahme. Run XI erweitert nicht die reine Bilddetektion, sondern
den allgemeinen Registrierungsraum für vorhandene Polygonpfad-Stroke-Gradienten.
Der Perception-Lerneffekt bleibt auf Ebene der Seed-Quelle `nur Sonderfall`, die
nachgelagerte Gradient-Offset-Registrierung ist aber katalogfrei generalisiert.

## Validierung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_stroke_gradient_offsets_with_eighth_yoctofine_probe` läuft grün mit `1 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. ICC_MAX_QUALITY_PASSES=1 timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-dlg0021-runXI --start DLG0021 --end DLG0021 --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; der isolierte DLG0021-Einzellauf meldet `Mean-Delta²=16622.357422` und `Fehler/Pixel=0.076626`.

## Ergebnis

Run XI schließt den dokumentierten DLG0021-Feinschritt ab. Polygonpfad-
Stroke-Gradienten können nun eine eighth-yoctofeine Offset-Registrierung nutzen;
der isolierte DLG0021-Einzellauf sinkt gegenüber der bisherigen Plan-B-Metrik
von `Mean-Delta²=16540.876953` im besten dokumentierten Quarter-Yoctofine-Lauf
nicht weiter, bleibt aber gegenüber dem ersten Run-XI-Pass stabil im gleichen
Restfehlerband. Das nächste Arbeitspaket kann in der aktiven Plan-B-Rotation zu
`GE1410_L` wechseln oder weitere allgemeine Gradient-/Antialiasing-
Feinregistrierung prüfen.
