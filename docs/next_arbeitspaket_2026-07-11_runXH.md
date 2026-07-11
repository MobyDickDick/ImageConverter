# Nächstes Arbeitspaket – GE9013_1M Half-Yoctofine-Warmfill-Probe Run XH (2026-07-11)

Run XH rotiert nach `docs/next_arbeitspaket_2026-07-10_runXG.md` in der
aktiven Plan-B-Kandidatenliste zu `GE9013_1M`. Der Fokus bleibt katalogfrei:
Die allgemeine `ColorPatch`-/`RectBorder`-Farbregistrierung erhält eine weitere
warme Zwischenfarbe für BackBottom-ähnliche helle Rechteckfüllungen.

## Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt bei rechteckigen `ColorPatch`-
  und `RectBorder`-Füllflächen zusätzlich `#f3bab8` als half-yoctofeine warme
  Zwischenfarbe zwischen den bestehenden BackBottom-Farbankern.
- Ein neuer Helper-Test sichert, dass diese Probe ausschließlich über den
  regulären Optimiererpfad und nur bei sinkendem Fehler akzeptiert wird.
- Die Änderung hängt weder an `GE9013_1M` noch an eine andere Runtime-Bild-ID.

## Plan-B-/Perception-Lerneffekt

`GE9013_1M` bleibt ein beschreibungsbasierter BackBottom-/hellgraues-Quadrat-
Contract mit rechteckiger Füllfläche und Kontur. Run XH erweitert nicht die
reine Bilddetektion, sondern den allgemeinen Registrierungsraum für vorhandene
rechteckige Füllelemente. Der Perception-Lerneffekt bleibt auf Ebene der
Seed-Quelle `nur Sonderfall`, die nachgelagerte Warmfill-Registrierung ist aber
katalogfrei generalisiert.

## Validierung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rect_to_half_yoctofine_warm_light_fill` läuft grün mit `1 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. ICC_MAX_QUALITY_PASSES=1 timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ge9013-runXH --start GE9013_1M --end GE9013_1M --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; der isolierte GE9013_1M-Einzellauf verbessert sich auf `Mean-Delta²=12767.278320` und `Fehler/Pixel=0.038889`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün mit `0 occurrences`.

## Ergebnis

Run XH schließt den dokumentierten GE9013_1M-Feinschritt ab. Rechteckige
Füllflächen können nun eine zusätzliche warme Zwischenfarbe nutzen; der
isolierte GE9013_1M-Einzellauf sinkt gegenüber der bisherigen Plan-B-Metrik von
`Mean-Delta²=12989.524414` auf `Mean-Delta²=12767.278320`. Das nächste
Arbeitspaket kann in der aktiven Plan-B-Rotation wieder zu `DLG0021` wechseln
oder weitere allgemeine BackBottom-/Rechteck-Feinregistrierung prüfen.
