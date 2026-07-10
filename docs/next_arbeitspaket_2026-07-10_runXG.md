# Nächstes Arbeitspaket – GE9012_6M Half-Yoctofine-Opacity-Probes Run XG (2026-07-10)

Run XG rotiert nach `docs/next_arbeitspaket_2026-07-10_runXF.md` in der
aktiven Plan-B-Kandidatenliste zu `GE9012_6M`. Der Fokus bleibt katalogfrei:
Die allgemeinen `ColorPatch`- und `RectBorder`-Opacity-Probes werden um eine
half-yoctofeine Zwischenstufe nahe der bisherigen BackBottom-Zielopacity
ergänzt.

## Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt bei `ColorPatch.fill_opacity`
  zusätzlich `0.9827880859375` als half-yoctofeine Zwischenstufe unterhalb von
  `0.9828125`.
- Die allgemeine Geometry-IR-Optimierung probt bei `RectBorder.stroke_opacity`
  zusätzlich `0.9828369140625` als half-yoctofeine Zwischenstufe oberhalb von
  `0.9828125`.
- Zwei neue Helper-Tests sichern, dass die neuen Opacity-Probes nur über den
  regulären Optimiererpfad und nur bei sinkendem Fehler akzeptiert werden.
- Die Änderung hängt weder an `GE9012_6M` noch an eine andere Runtime-Bild-ID.

## Plan-B-/Perception-Lerneffekt

`GE9012_6M` bleibt ein beschreibungsbasierter BackBottom-/hellgraues-Quadrat-
Contract. Run XG erweitert nicht die reine Bilddetektion, sondern den
allgemeinen Registrierungsraum für vorhandene rechteckige Füll- und
Konturelemente. Der Perception-Lerneffekt bleibt auf Ebene der Seed-Quelle
`nur Sonderfall`, die nachgelagerte Opacity-Registrierung ist aber katalogfrei
generalisiert.

## Validierung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_color_patch_opacity_with_half_yoctofine_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rect_border_stroke_opacity_with_half_yoctofine_probe` läuft grün mit `2 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. ICC_MAX_QUALITY_PASSES=1 timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ge9012-runXG --start GE9012_6M --end GE9012_6M --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; der isolierte GE9012_6M-Einzellauf bleibt stabil bei `Mean-Delta²=15386.639648` und `Fehler/Pixel=0.044122`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün mit `0 occurrences`.

## Lokaler Gesamt-Test zum Hochladen

Für die lokale Reproduktion kann folgendes Testpaket gesammelt werden:

```bash
PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q \
  tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_color_patch_opacity_with_half_yoctofine_probe \
  tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rect_border_stroke_opacity_with_half_yoctofine_probe
PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py
PYTHONPATH=vendor/linux-py310/site-packages:. ICC_MAX_QUALITY_PASSES=1 timeout 120 python -m src.iCCModules.imageCompositeConverterCli \
  --input-dir artifacts/images_to_convert \
  --output-dir /tmp/ic-ge9012-runXG \
  --start GE9012_6M --end GE9012_6M \
  --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml \
  --deterministic-order
```

## Ergebnis

Run XG schließt den dokumentierten GE9012_6M-Feinschritt auf Code- und
Helper-Test-Ebene ab. Rechteckige Füll- und Konturelemente können nun eine
half-yoctofeine Opacity-Zwischenregistrierung nutzen. Das nächste Arbeitspaket
kann in der aktiven Plan-B-Rotation zu `GE9013_1M` wechseln oder weitere
allgemeine BackBottom-/Rechteck-Feinregistrierung prüfen.
