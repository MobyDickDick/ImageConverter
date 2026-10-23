# Nächstes Arbeitspaket – GE9013_1M RectBorder-Stroke-Width-Probes Run UE (2026-06-30)

Run UE rotiert nach dem GE9012_6M-Opacity-Schritt aus Run UD auf den aktiven
Plan-B-Kandidaten `GE9013_1M` aus `PLAN_B_KANDIDATEN.md`. Der Fokus bleibt
katalogfrei: rechteckige Rahmenprimitive erhalten feine absolute
Stroke-Width-Probes, damit BackBottom-/Light-Grey-Square-Contracts kleine
Antialiasing- und Konturstärken-Abweichungen ohne Bild-ID-Sonderfall bewerten
können.

## 1) Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt für `RectBorder`-Elemente mit
  vorhandener `stroke_width` zusätzlich `stroke_width ± 0.005`.
- Die neuen Probes ergänzen die vorhandenen relativen `0.85`-/`1.15`-Probes und
  werden wie alle Kandidaten nur übernommen, wenn der gerenderte Fehler strikt
  sinkt.
- Die Änderung ist elementweise, deterministisch und katalogfrei; sie koppelt
  weder an `GE9013_1M` noch an eine andere Runtime-Bild-ID.

## 2) Perception-Lerneffekt

`GE9013_1M` bleibt `nur Sonderfall` auf Ebene des beschreibungsbasierten
BackBottom-/Light-Grey-Square-Contracts. Run UE erweitert nicht die initiale
Bilddetektion, sondern den allgemeinen Optimierungsraum für vorhandene
rechteckige `RectBorder`-Primitive: Sobald ein Rahmen im Geometry-IR-Pfad
vorliegt, kann eine feinere Konturstärke ohne Katalogbindung bewertet werden.

## 3) Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py` läuft grün mit `25 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün und bestätigt weiterhin `0` Runtime-ID-Vorkommen.
- `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ge9013-runUE --start GE9013_1M --end GE9013_1M --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; die isolierte GE9013_1M-Metrik bleibt stabil bei `Mean-Delta²=12989.524414` und `Fehler/Pixel=0.035766`.

## 4) Ergebnis / nächster Schritt

Run UE schließt den dokumentierten GE9013_1M-Feinschritt ab. Rechteckige
Geometry-IR-Rahmen können nun katalogfrei feine absolute Stroke-Width-Varianten
optimieren; der isolierte GE9013_1M-Einzellauf bleibt stabil. Das nächste
Arbeitspaket kann in der aktiven Plan-B-Rotation wieder zu `DLG0021` wechseln
oder weitere allgemeine Rechteck-/Antialiasing-Probes untersuchen.
