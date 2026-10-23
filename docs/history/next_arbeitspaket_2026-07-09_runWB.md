# Nächstes Arbeitspaket – GE9013_1M Yoctofine-Opacity-Probes Run WB (2026-07-09)

Run WB rotiert nach dem GE9012_6M-Zeptofine-Opacity-Schritt aus Run WA zum
aktiven Plan-B-Kandidaten `GE9013_1M`. Der Fokus bleibt katalogfrei: Die bereits
allgemeinen `ColorPatch`- und `RectBorder`-Opacity-Probes werden um eine
yoctofeine Zwischenstufe ergänzt, damit helle BackBottom-/Quadratflächen noch
kleinere Mischungs- und Antialiasing-Unterschiede ohne Bild-ID-Sonderfall
bewerten können.

## 1) Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt für `ColorPatch.fill_opacity`
  jetzt zusätzlich den yoctofeinen Zwischenwert `0.982763671875`.
- Für `RectBorder.stroke_opacity` wird entsprechend der yoctofeine Zwischenwert
  `0.982861328125` ergänzt.
- Die Änderung ist deterministisch und katalogfrei; sie koppelt weder an
  `GE9013_1M` noch an eine andere Runtime-Bild-ID.

## 2) Perception-Lerneffekt

`GE9013_1M` bleibt ein beschreibungsbasierter BackBottom-/Light-Grey-Square-
Contract. Run WB erweitert nicht die Detektion, sondern den allgemeinen
Optimierungsraum für bereits vorhandene rechteckige Füll- und Konturprimitive,
die aus neutralen Beschreibungs- oder Perception-Seeds entstehen.

## 3) Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_color_patch_opacity_with_yoctofine_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rect_border_stroke_opacity_with_yoctofine_probe` läuft grün mit `2 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün und bestätigt weiterhin `0` Runtime-ID-Vorkommen.
- `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ge9013-runWB --start GE9013_1M --end GE9013_1M --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; der isolierte GE9013_1M-Einzellauf bleibt stabil bei `Mean-Delta²=12989.524414` und `Fehler/Pixel=0.035766`.

## 4) Ergebnis / nächster Schritt

Run WB schließt den dokumentierten GE9013_1M-Feinschritt ab. Rechteckige
Füllungen und Konturen können nun katalogfrei yoctofeine Opacity-Zwischenwerte
bewerten; der isolierte GE9013_1M-Einzellauf bleibt metrisch stabil. Das nächste
Arbeitspaket kann in der aktiven Plan-B-Rotation zu `DLG0021` wechseln oder
weiteres allgemeines Rect-/Opacity-Feintuning prüfen.
