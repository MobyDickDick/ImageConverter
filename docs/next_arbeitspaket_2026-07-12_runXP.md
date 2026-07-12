# Nächstes Arbeitspaket – SE0041_1 Half-Yoctofine-Rule-Stroke-Probes Run XP (2026-07-12)

Run XP rotiert nach `docs/next_arbeitspaket_2026-07-12_runXO.md` zurück zu
`SE0041_1`. Der Fokus bleibt katalogfrei: Die allgemeinen
`RectBorder`-/`HorizontalRule`-/`VerticalRule`-Stroke-Width-Probes erhalten eine
half-yoctofeine absolute Zwischenstufe für antialiasing-empfindliche
Square-Badge-Konturen.

## Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt bei `RectBorder`,
  `HorizontalRule` und `VerticalRule`-`stroke_width` zusätzlich
  `±0.00000244140625` als absolutes Delta.
- Zwei neue Helper-Tests sichern die Zwischenstufe separat für rechteckige
  Konturen und Rule-Arme ab.
- Die Änderung ist nicht an `SE0041_1` oder eine andere Runtime-Bild-ID
  gekoppelt.

## Plan-B-/Perception-Lerneffekt

`SE0041_1` bleibt ein beschreibungsbasierter Square-Badge-Contract mit roter
Viereck-Kopfkontur, senkrechtem Stem und waagrechtem Arm. Run XP erweitert
keinen Sonderfall, sondern verfeinert den allgemeinen Registrierungsraum für
bereits vorhandene Rule-/RectBorder-Primitive. Der Perception-Lerneffekt bleibt
`generalisiert`.

## Validierung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rect_border_stroke_width_with_half_yoctofine_absolute_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rule_stroke_width_with_half_yoctofine_absolute_probe` läuft grün mit `2 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. ICC_MAX_QUALITY_PASSES=1 timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-se0041-runXP --start SE0041_1 --end SE0041_1 --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; der isolierte `SE0041_1`-Einzellauf bleibt semantisch erfolgreich und meldet in dieser Umgebung `Mean-Delta²=99562.164062` bei `Fehler/Pixel=0.121547`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün mit `0 occurrences`.

## Ergebnis / nächster Schritt

Run XP schließt den dokumentierten SE0041_1-Feinschritt auf Code-, Test- und
isolierter Recheck-Ebene ab. Das nächste Arbeitspaket kann in der aktiven
Plan-B-Rotation zu `GE9012_6M` wechseln oder weiteres allgemeines
Rule-/RectBorder-Antialiasing-Feintuning prüfen.
