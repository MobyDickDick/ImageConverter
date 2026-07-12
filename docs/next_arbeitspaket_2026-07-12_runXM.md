# Nächstes Arbeitspaket – GE9013_1M Quarter-Yoctofine-Warmfill-Probe Run XM (2026-07-12)

Run XM rotiert nach `docs/next_arbeitspaket_2026-07-12_runXL.md` in der aktiven Plan-B-Kandidatenliste zu `GE9013_1M`. Der Fokus bleibt katalogfrei: Die allgemeine `ColorPatch`-/`RectBorder`-Farbregistrierung erhält eine quarter-yoctofeine warme Zwischenfarbe für BackBottom-ähnliche helle Rechteckfüllungen.

## 1) Implementierung

- Die allgemeine Geometry-IR-Optimierung probt bei rechteckigen `ColorPatch`- und `RectBorder`-Füllflächen zusätzlich `#f3bab9` als quarter-yoctofeine warme Zwischenfarbe neben den bestehenden BackBottom-Farbankern.
- Ein neuer Detailtest sichert, dass diese Probe über den regulären Optimiererpfad und nur bei sinkendem Fehler akzeptiert wird.
- Die Änderung hängt weder an `GE9013_1M` noch an eine andere Runtime-Bild-ID.

## 2) Plan-B-/Perception-Lerneffekt

`GE9013_1M` bleibt ein beschreibungsbasierter BackBottom-/hellgraues-Quadrat-Contract mit rechteckiger Füllfläche und Kontur. Run XM erweitert nicht die reine Bilddetektion, sondern den allgemeinen Registrierungsraum für vorhandene rechteckige Füllelemente. Der Perception-Lerneffekt bleibt auf Ebene der Seed-Quelle `nur Sonderfall`; die nachgelagerte Warmfill-Registrierung ist weiterhin katalogfrei generalisiert.

## 3) Reproduzierbare Checks

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rect_to_quarter_yoctofine_warm_light_fill` läuft grün mit `1 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün mit `0 occurrences`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. ICC_MAX_QUALITY_PASSES=1 timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ge9013-runXM --start GE9013_1M --end GE9013_1M --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; der isolierte `GE9013_1M`-Einzellauf bleibt erfolgreich bei `Mean-Delta²=12839.200195` und `Fehler/Pixel=0.039071` im Qualitätspass.

## 4) Ergebnis / nächster Schritt

Run XM schließt den dokumentierten GE9013_1M-Feinschritt auf Code-, Test- und isolierter Recheck-Ebene ab. Rechteckige Füllflächen können nun eine quarter-yoctofeine warme Zwischenfarbe nutzen. Das nächste Arbeitspaket kann in der aktiven Plan-B-Rotation wieder zu `DLG0021` wechseln oder weiteres allgemeines BackBottom-/Rechteck-Feintuning prüfen.
