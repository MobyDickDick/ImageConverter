# Nächstes Arbeitspaket – SE0041_1 Quarter-Yoctofine-Rule-Stroke-Probes Run XK (2026-07-11)

Run XK arbeitet nach Run XJ den nächsten dokumentierten Plan-B-Schritt in der aktiven Rotation ab und bestätigt zusätzlich den vom Nutzer angefragten Ad-hoc-Refresh für `AC0838_M`. Der Fokus bleibt katalogfrei: Die allgemeinen `RectBorder`-/`HorizontalRule`-/`VerticalRule`-Stroke-Width-Probes erhalten eine quarter-yoctofeine absolute Zwischenstufe für antialiasing-empfindliche Square-Badge-Konturen.

## 1) Implementierung

- Die allgemeine Geometry-IR-Optimierung probt bei `RectBorder`, `HorizontalRule` und `VerticalRule`-`stroke_width` zusätzlich `±0.0000048828125`.
- Die Probe ist bewusst nicht an `SE0041_1`, `AC0838_M` oder eine andere Runtime-Bild-ID gekoppelt.
- Zwei Detailtests sichern die neue Zwischenstufe separat für rechteckige Konturen und Rule-Arme ab.

## 2) Plan-B-/Perception-Lerneffekt

`SE0041_1` bleibt ein beschreibungsbasierter Square-Badge-Contract mit roter Viereck-Kopfkontur, senkrechtem Stem und waagrechtem Arm. Run XK erweitert keinen Sonderfall, sondern macht die vorhandenen katalogfreien Rule-/RectBorder-Stroke-Probes noch feiner. Der Perception-Lerneffekt bleibt damit `generalisiert` für die bereits vorhandenen Rule-/RectBorder-Primitive.

## 3) AC0838_M Ad-hoc-Refresh

Der angefragte `AC0838_M`-Plan-B-Refresh wurde isoliert gegen `artifacts/images_to_convert/nonconvertable/AC0838_M.jpg` ausgeführt. Der Lauf bleibt im semantischen VOC-Badge-Pfad (`SEMANTIC: senkrechter Strich oben vom Kreis`, `SEMANTIC: Kreis + Buchstabe VOC`, `SEMANTIC: waagrechter Strich rechts vom Kreis`) und endet erfolgreich mit Exit `0`. Die beste Validierungsrunde meldet erneut `Mean-Delta²=5773.821`; der finale CLI-Qualitätsbericht liegt bei `Fehler/Pixel=0.044755` und `Mean-Delta²=8693.271484` im ersten Qualitätspass.

## 4) Reproduzierbare Checks

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rect_border_stroke_width_with_quarter_yoctofine_absolute_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rule_stroke_width_with_quarter_yoctofine_absolute_probe` läuft grün mit `2 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. ICC_MAX_QUALITY_PASSES=1 timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert/nonconvertable --output-dir /tmp/ic-ac0838m-runXK --start AC0838_M --end AC0838_M --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; der isolierte `AC0838_M`-Refresh bleibt semantisch erfolgreich.
- `PYTHONPATH=vendor/linux-py310/site-packages:. ICC_MAX_QUALITY_PASSES=1 timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-se0041-runXK --start SE0041_1 --end SE0041_1 --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; der isolierte `SE0041_1`-Einzellauf bleibt stabil bei `Mean-Delta²=2436.707764`.

## 5) Ergebnis / nächster Schritt

Run XK schließt den dokumentierten SE0041_1-Feinschritt ab und erledigt den angefragten `AC0838_M`-Refresh. Das nächste Arbeitspaket kann in der aktiven Plan-B-Rotation zu `GE9012_6M` wechseln oder weiteres allgemeines Rule-/RectBorder-Antialiasing-Feintuning prüfen.
