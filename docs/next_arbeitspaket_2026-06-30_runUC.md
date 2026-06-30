# Nächstes Arbeitspaket – SE0041_1 Rect/ColorPatch-BBox-Subpixel-Probes Run UC (2026-06-30)

Run UC rotiert nach dem GE1410_L-Punktfeinschritt aus Run UB auf den
nächstpriorisierten aktiven Plan-B-Kandidaten `SE0041_1` aus
`PLAN_B_KANDIDATEN.md`. Der Fokus bleibt katalogfrei: rechteckige und
farbflächenbasierte Geometry-IR-Elemente erhalten feinere lokale
Bounding-Box-Probes, damit Square-Badge-Kopf, Kontur und Flächenkanten ohne
Bild-ID-Sonderfall subpixelgenauer registriert werden können.

## 1) Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt für `ColorPatch`- und
  `RectBorder`-Bounding-Box-Koordinaten zusätzlich zu ±0.01/±0.02 nun auch
  neutrale ±0.005-Subpixel-Schritte.
- Die Erweiterung bleibt elementweise, deterministisch und katalogfrei; sie
  greift für alle rechteckigen Farbfelder und Konturen und koppelt nicht an
  `SE0041_1` oder andere Runtime-Bild-IDs.
- Ein gezielter Helper-Test sichert ab, dass ein strikt verbessernder
  ±0.005-BBox-Kandidat akzeptiert wird.

## 2) Perception-Lerneffekt

`SE0041_1` bleibt `nur Sonderfall` auf der Ebene der initialen manuellen
Square-Badge-Seed-Annahme, profitiert aber von der allgemeinen Optimierung:
Kopf- und Konturprimitive können als neutrale `RectBorder`-/`ColorPatch`-
Elemente feiner registriert werden, sobald sie im Geometry-IR-Pfad vorliegen.
Run UC erweitert nicht die Perception-Erkennung selbst, sondern den
katalogfreien Optimierungsraum für rechteckige Primitive.

## 3) Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rect_bbox_with_subpixel_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_neutral_rect_fill_color` läuft grün mit `2 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün und bestätigt weiterhin `0` Runtime-ID-Vorkommen.
- `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-se0041-runUC --start SE0041_1 --end SE0041_1 --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; die isolierte SE0041_1-Metrik bleibt stabil bei `Mean-Delta²=2436.707764` und `Fehler/Pixel=0.015932`.

## 4) Ergebnis / nächster Schritt

Run UC schließt den dokumentierten SE0041_1-Feinschritt ab. Die neuen feinen
`RectBorder`-/`ColorPatch`-BBox-Probes sind abgesichert und verändern die
isolierte SE0041_1-Metrik nicht regressiv. Das nächste Arbeitspaket kann in der
aktiven Plan-B-Rotation zu `GE9012_6M` wechseln oder weitere katalogfreie
Rechteck-/Antialiasing-Probes untersuchen.
