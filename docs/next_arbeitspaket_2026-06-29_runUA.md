# Nächstes Arbeitspaket – DLG0021 Stroke-Gradient-Offset-Recheck Run UA (2026-06-29)

Run UA arbeitet den in `PLAN_B_KANDIDATEN.md` bereits dokumentierten nächsten
DLG0021-Feinschritt nach Run TZ ab: Die neu ergänzten, katalogfreien
`PolygonPath`-Stroke-Gradient-Offset-Probes werden in einem isolierten
DLG0021-Lauf gegen den aktuellen Description-Geometry-IR-Pfad gemessen.

## 1) Umsetzung

- Die bestehende allgemeine Geometry-IR-Optimierung enthält nun neutrale
  Prozent-Offset-Probes für `stroke_gradient.stops[*].offset` von
  `PolygonPath`-Elementen.
- Der isolierte DLG0021-Recheck bestätigt, dass der neue Probe-Raum keine neue
  Bild-ID-Kopplung benötigt und weiterhin über den beschreibungsbasierten
  `ColorPatch`-/`RectBorder`-/`PolygonPath`-Contract läuft.
- Für den aktuellen DLG0021-Seed wird kein weiterer strikt verbessernder
  Offset-Kandidat übernommen; die Pixelmetrik bleibt gegenüber Run TY stabil.

## 2) Perception-Lerneffekt

`DLG0021` bleibt `nur Sonderfall`: Die reine Bilddetektion liefert weiterhin
keinen stabilen generischen Checkbox-/Checkmark-Seed. Run UA verallgemeinert
nicht die Perception-Erkennung selbst, sondern prüft den katalogfreien
Beschreibungspfad mit den zusätzlichen Gradienten-Offset-Probes.

## 3) Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_stroke_gradient_offsets tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_stroke_gradient_stops` läuft grün mit `2 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün und bestätigt weiterhin `0` Runtime-ID-Vorkommen.
- `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-dlg0021-runUA --start DLG0021 --end DLG0021 --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; die isolierte DLG0021-Metrik bleibt bei `Fehler/Pixel=0.077702` und `Mean-Delta²=17056.199219`.

## 4) Ergebnis / nächster Schritt

Run UA schließt den dokumentierten DLG0021-Gradient-Offset-Recheck ab. Die neuen
Offset-Probes sind abgesichert, bringen für den aktuellen DLG0021-Seed aber
keine zusätzliche isolierte Verbesserung. Das nächste Arbeitspaket kann daher in
der Rotation wieder zu `GE1410_L` oder `SE0041_1` wechseln oder optional weiteres
DLG0021-Antialiasing-/Kontur-Feintuning untersuchen.
