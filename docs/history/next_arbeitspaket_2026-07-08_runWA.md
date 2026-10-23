# Nächstes Arbeitspaket – GE9012_6M Zeptofine-Opacity-Probes Run WA (2026-07-08)

Run WA rotiert nach dem SE0041_1-Yoctofine-Rule-Stroke-Schritt aus Run VZ zum
aktiven Plan-B-Kandidaten `GE9012_6M`. Der Fokus bleibt katalogfrei: Die bereits
allgemeinen `ColorPatch`- und `RectBorder`-Opacity-Probes werden um eine
zeptofeine Stufe ergänzt, damit helle BackBottom-/Quadratflächen minimale
Antialiasing- und Mischungsunterschiede weiterhin ohne Bild-ID-Sonderfall
bewerten können.

## 1) Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt für `ColorPatch.fill_opacity`
  jetzt zusätzlich den zeptofeinen Zwischenwert `0.98271484375`.
- Für `RectBorder.stroke_opacity` wird entsprechend der zeptofeine Zwischenwert
  `0.98291015625` ergänzt.
- Die Änderung ist deterministisch und katalogfrei; sie koppelt weder an
  `GE9012_6M` noch an eine andere Runtime-Bild-ID.

## 2) Perception-Lerneffekt

`GE9012_6M` bleibt ein beschreibungsbasierter BackBottom-/Light-Grey-Square-
Contract. Run WA erweitert nicht die Detektion, sondern den allgemeinen
Optimierungsraum für bereits vorhandene rechteckige Füll- und Konturprimitive,
die aus neutralen Beschreibungs- oder Perception-Seeds entstehen.

## 3) Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_color_patch_opacity_with_zeptofine_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rect_border_stroke_opacity_with_zeptofine_probe` läuft grün mit `2 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün und bestätigt weiterhin `0` Runtime-ID-Vorkommen.
- `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ge9012-runWA --start GE9012_6M --end GE9012_6M --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; der isolierte GE9012_6M-Einzellauf bleibt stabil bei `Mean-Delta²=15386.639648` und `Fehler/Pixel=0.044122`.

## 4) Ergebnis / nächster Schritt

Run WA schließt den dokumentierten GE9012_6M-Feinschritt ab. Rechteckige
Füllungen und Konturen können nun katalogfrei zeptofeine Opacity-Zwischenwerte
bewerten; der isolierte GE9012_6M-Einzellauf bleibt metrisch stabil. Das nächste
Arbeitspaket kann in der aktiven Plan-B-Rotation zu `GE9013_1M` wechseln oder
weiteres allgemeines Rect-/Opacity-Feintuning prüfen.
