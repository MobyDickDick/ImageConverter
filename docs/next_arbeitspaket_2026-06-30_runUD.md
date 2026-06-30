# Nächstes Arbeitspaket – GE9012_6M Rect/ColorPatch-Opacity-Probes Run UD (2026-06-30)

Run UD rotiert nach dem SE0041_1-Subpixel-Schritt aus Run UC auf den aktiven
Plan-B-Kandidaten `GE9012_6M` aus `PLAN_B_KANDIDATEN.md`. Der Fokus bleibt
katalogfrei: rechteckige Geometry-IR-Primitive erhalten neutrale
Opacity-Probes und der SVG-Renderer emittiert diese Werte für `RectBorder` und
`ColorPatch`, damit helle BackBottom-/Quadrat-Flächen später ohne Bild-ID-
Sonderfall weichere Kanten- und Flächenmischungen testen können.

## 1) Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt für `ColorPatch` und
  `RectBorder` jetzt neutrale `fill_opacity`- und `stroke_opacity`-Werte.
- Der Geometry-IR-SVG-Renderer gibt `fill-opacity` und `stroke-opacity` für
  rechteckige Primitive aus, wenn deren Wert kleiner als `1.0` ist.
- Die Änderung ist elementweise, deterministisch und katalogfrei; sie koppelt
  weder an `GE9012_6M` noch an eine andere Runtime-Bild-ID.

## 2) Perception-Lerneffekt

`GE9012_6M` bleibt `nur Sonderfall` auf der Ebene des beschreibungsbasierten
BackBottom-/Light-Grey-Square-Contracts. Run UD erweitert nicht die initiale
Bilddetektion, sondern den allgemeinen Optimierungsraum für vorhandene
rechteckige `RectBorder`-/`ColorPatch`-Primitive: Sobald diese Primitive im
Geometry-IR-Pfad vorliegen, können transparente Füll- und Konturvarianten ohne
Katalogbindung bewertet werden.

## 3) Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rect_opacity_with_neutral_probe tests/detailtests/test_geometry_ir_helpers.py::test_render_geometry_ir_rects_emit_opacity_attributes` läuft grün mit `2 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün und bestätigt weiterhin `0` Runtime-ID-Vorkommen.
- `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ge9012-runUD --start GE9012_6M --end GE9012_6M --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; die isolierte GE9012_6M-Metrik bleibt stabil bei `Mean-Delta²=15386.639648` und `Fehler/Pixel=0.044122`.

## 4) Ergebnis / nächster Schritt

Run UD schließt den dokumentierten GE9012_6M-Feinschritt ab. Rechteckige
Geometry-IR-Primitive können nun katalogfrei Opacity-Varianten rendern und
optimieren; der isolierte GE9012_6M-Einzellauf bleibt stabil. Das nächste
Arbeitspaket kann in der aktiven Plan-B-Rotation zu `GE9013_1M` wechseln oder
weitere allgemeine Rechteck-/Antialiasing-Probes untersuchen.
