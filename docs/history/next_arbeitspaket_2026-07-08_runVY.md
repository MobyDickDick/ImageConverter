# Nächstes Arbeitspaket – GE1410_L Yoctofine-PolygonPath-Probes Run VY (2026-07-08)

Run VY rotiert nach dem DLG0021-Zeptofine-Gradient-Schritt aus Run VW wieder
zum aktiven Plan-B-Kandidaten `GE1410_L`. Der Fokus bleibt katalogfrei: Die
bereits allgemeinen `PolygonPath`-Punkt- und Stroke-Width-Probes werden um eine
noch feinere yoctofeine Stufe ergänzt.

## 1) Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt für `PolygonPath.points` jetzt
  zusätzlich yoctofeine Subpixel-Deltas von `±0.000009765625` je Koordinate.
- Dieselbe yoctofeine absolute Stufe wird für `PolygonPath.stroke_width`
  ergänzt, damit Antialiasing-sensitive Dreiecks-/Linienkonturen weiterhin ohne
  katalogspezifische Sonderfälle lokal nachregistriert werden können.
- Die Änderung ist deterministisch und katalogfrei; sie koppelt weder an
  `GE1410_L` noch an eine andere Runtime-Bild-ID.

## 2) Perception-Lerneffekt

Der Lerneffekt für `GE1410_L` bleibt `generalisiert`: Der vorhandene
Diagramm-/Dreieck-Contract nutzt weiterhin neutrale `PolygonPath`-Elemente. Run
VY erweitert ausschließlich den allgemeinen Optimierungsraum für vorhandene
Pfadpunkte und Pfadkonturstärken.

## 3) Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_points_with_yoctofine_subpixel_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_stroke_width_with_yoctofine_absolute_probe` läuft grün mit `2 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün und bestätigt weiterhin `0` Runtime-ID-Vorkommen.
- `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ge1410-runVY --start GE1410_L --end GE1410_L --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; der isolierte GE1410_L-Einzellauf bleibt stabil bei `Mean-Delta²=759.441589` und `Fehler/Pixel=0.010179`.

## 4) Ergebnis / nächster Schritt

Run VY schließt den dokumentierten GE1410_L-Feinschritt ab. `PolygonPath`-
Punkte und -Konturstärken können nun katalogfrei yoctofeine Nachbarwerte
bewerten; der isolierte GE1410_L-Einzellauf bleibt stabil. Das nächste
Arbeitspaket kann in der aktiven Plan-B-Rotation zu `SE0041_1` wechseln oder
weiteres allgemeines Antialiasing-/PolygonPath-Feintuning prüfen.
