# Nächstes Arbeitspaket – GE9012_6M Quarter-Yoctofine-Opacity-Probes Run XL (2026-07-12)

Run XL arbeitet nach Run XK den nächsten dokumentierten Plan-B-Schritt in der aktiven Rotation ab. Der Fokus bleibt katalogfrei: Die allgemeinen `ColorPatch`- und `RectBorder`-Opacity-Probes erhalten eine quarter-yoctofeine Zwischenstufe nahe der bisherigen BackBottom-Zielopacity.

## 1) Implementierung

- Die allgemeine Geometry-IR-Optimierung probt bei `ColorPatch.fill_opacity` zusätzlich `0.98280029296875` als quarter-yoctofeine Zwischenstufe unterhalb von `0.9828125`.
- Die allgemeine Geometry-IR-Optimierung probt bei `RectBorder.stroke_opacity` zusätzlich `0.98282470703125` als quarter-yoctofeine Zwischenstufe oberhalb von `0.9828125`.
- Zwei Detailtests sichern die neuen Opacity-Probes separat für rechteckige Füllflächen und Konturen ab.
- Die Änderung hängt weder an `GE9012_6M` noch an eine andere Runtime-Bild-ID.

## 2) Plan-B-/Perception-Lerneffekt

`GE9012_6M` bleibt ein beschreibungsbasierter BackBottom-/hellgraues-Quadrat-Contract. Run XL erweitert nicht die reine Bilddetektion, sondern den allgemeinen Registrierungsraum für vorhandene rechteckige Füll- und Konturelemente. Der Perception-Lerneffekt bleibt auf Ebene der Seed-Quelle `nur Sonderfall`; die nachgelagerte Opacity-Registrierung ist weiterhin katalogfrei generalisiert.

## 3) Reproduzierbare Checks

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_color_patch_opacity_with_quarter_yoctofine_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rect_border_stroke_opacity_with_quarter_yoctofine_probe` läuft grün mit `2 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün mit `0 occurrences`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. ICC_MAX_QUALITY_PASSES=1 timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ge9012-runXL --start GE9012_6M --end GE9012_6M --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; der isolierte `GE9012_6M`-Einzellauf bleibt erfolgreich bei `Mean-Delta²=15506.059570` und `Fehler/Pixel=0.049269` im Qualitätspass.

## 4) Ergebnis / nächster Schritt

Run XL schließt den dokumentierten GE9012_6M-Feinschritt auf Code-, Test- und isolierter Recheck-Ebene ab. Rechteckige Füll- und Konturelemente können nun eine quarter-yoctofeine Opacity-Zwischenregistrierung nutzen. Das nächste Arbeitspaket kann in der aktiven Plan-B-Rotation zu `GE9013_1M` wechseln oder weiteres allgemeines BackBottom-/Rechteck-Feintuning prüfen.
