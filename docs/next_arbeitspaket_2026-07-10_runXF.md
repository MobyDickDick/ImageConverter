# Nächstes Arbeitspaket – SE0041_1 Half-Yoctofine-Rule-/RectBorder-Stroke-Probes Run XF (2026-07-10)

Run XF rotiert nach `docs/next_arbeitspaket_2026-07-10_runXE.md` in der
aktiven Plan-B-Kandidatenliste zu `SE0041_1`. Der Fokus bleibt katalogfrei:
Die allgemeinen `RectBorder`-, `HorizontalRule`- und `VerticalRule`-
`stroke_width`-Probes werden um eine half-yoctofeine absolute Zwischenstufe
ergänzt.

## Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt bei `RectBorder`,
  `HorizontalRule` und `VerticalRule` zusätzlich `±0.000009765625` als absolute
  `stroke_width`-Verschiebung.
- Zwei neue Helper-Tests sichern, dass die neuen Probes sowohl für
  `RectBorder` als auch für Rule-Elemente nur über den regulären Optimiererpfad
  und nur bei sinkendem Fehler akzeptiert werden.
- Die Änderung hängt weder an `SE0041_1` noch an eine andere Runtime-Bild-ID.

## Plan-B-/Perception-Lerneffekt

`SE0041_1` bleibt ein beschreibungsbasierter Square-Badge-Contract aus
rechteckigem Kopf, grauer Kontur sowie horizontalen/vertikalen Rule-Stielen. Run
XF erweitert nicht die reine Bilddetektion, sondern den allgemeinen
Registrierungsraum für bereits vorhandene rechteckige Kontur- und Rule-Elemente.
Der Perception-Lerneffekt bleibt auf Ebene der Seed-Quelle `nur Sonderfall`, die
nachgelagerte Stroke-Registrierung ist aber katalogfrei generalisiert.

## Validierung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rect_border_stroke_width_with_half_yoctofine_absolute_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rule_stroke_width_with_half_yoctofine_absolute_probe` läuft grün mit `2 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. ICC_MAX_QUALITY_PASSES=1 timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-se0041-runXF --start SE0041_1 --end SE0041_1 --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; der isolierte SE0041_1-Einzellauf bleibt stabil bei `Mean-Delta²=2436.707764` und `Fehler/Pixel=0.015932`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün mit `0 occurrences`.

## Ergebnis

Run XF schließt den dokumentierten SE0041_1-Feinschritt ab. Rechteck- und
Rule-Konturen können nun eine half-yoctofeine absolute Stroke-Width-
Registrierung nutzen; der isolierte SE0041_1-Einzellauf bleibt grün und
metrisch stabil. Das nächste Arbeitspaket kann in der aktiven Plan-B-Rotation zu
`GE9012_6M` wechseln oder weitere allgemeine Rechteck-/BackBottom-
Antialiasing-Probes prüfen.
