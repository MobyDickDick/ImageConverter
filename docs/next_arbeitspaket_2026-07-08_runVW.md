# Nächstes Arbeitspaket – DLG0021 Zeptofine-Gradient-Offset-Probes Run VW (2026-07-08)

Run VW rotiert nach dem GE9013_1M-Femtofine-Warmfill-Schritt aus Run VV zurück
zum aktiven Plan-B-Kandidaten `DLG0021`. Der Fokus bleibt katalogfrei: Die
bereits allgemeinen `PolygonPath.stroke_gradient.stops[*].offset`-Probes werden
um eine noch feinere zeptofeine Stufe ergänzt.

## 1) Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt für vorhandene
  `stroke_gradient.stops` zusätzlich zeptofeine Offset-Deltas von `±0.00009765625`
  relativ zum aktuellen Stop-Offset.
- Die neue Stufe liegt zwischen dem attofeinen Schritt `±0.0001953125` und dem
  unveränderten Ausgangswert und wird wie alle Elementprobes nur übernommen,
  wenn der gerenderte Fehler im Elementschritt strikt sinkt.
- Die Änderung ist deterministisch und katalogfrei; sie koppelt weder an
  `DLG0021` noch an eine andere Runtime-Bild-ID.

## 2) Perception-Lerneffekt

`DLG0021` bleibt auf Ebene des initialen Checkbox-/Haken-Contracts ein
`nur Sonderfall`-Signal. Run VW erweitert nicht die Bilddetektion, sondern den
allgemeinen Optimierungsraum für bereits vorhandene `PolygonPath`-Konturen mit
Stroke-Gradienten, die aus neutralen Pfad- und Farbverlaufsbeschreibungen
entstehen.

## 3) Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_stroke_gradient_offsets_with_zeptofine_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_stroke_gradient_offsets_with_attofine_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_stroke_gradient_offsets_with_femtofine_probe` läuft grün mit `3 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün und bestätigt weiterhin `0` Runtime-ID-Vorkommen.
- `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-dlg0021-runVW --start DLG0021 --end DLG0021 --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; die isolierte DLG0021-Metrik bleibt stabil bei `Mean-Delta²=17056.199219` und `Fehler/Pixel=0.077702`.

## 4) Ergebnis / nächster Schritt

Run VW schließt den dokumentierten DLG0021-Feinschritt ab. `PolygonPath`-
Stroke-Gradient-Offsets können nun katalogfrei zeptofeine Nachbarwerte bewerten;
der isolierte DLG0021-Einzellauf bleibt stabil. Das nächste Arbeitspaket kann in
der aktiven Plan-B-Rotation zu `GE1410_L` wechseln oder weiteres allgemeines
Gradient-/PolygonPath-Feintuning prüfen.
