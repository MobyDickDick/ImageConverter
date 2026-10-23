# Nächstes Arbeitspaket – DLG0021 Checkmark-Geometrie Run SY (2026-06-26)

Run SY arbeitet das nach Run SX offene Pixel-Feintuning für den aktiven
Plan-B-Kandidaten `DLG0021` weiter ab. Fokus ist die Rasterregistrierung von
Checkbox und Haken, ohne den katalogfreien Checkbox-/Checkmark-Contract an eine
Bild-ID zu koppeln.

## Änderungen

- Die generische Checkbox-Bounding-Box wurde nach rechts/unten auf die im Raster
  sichtbare quadratische Fläche gezogen und von der vorher zu großen linken
  Registrierung entkoppelt.
- Die graue Haken-Umrandung und der grüne Gradient-Haken nutzen nun steilere,
  höher ansetzende Normalized-Points, damit der lange Schenkel näher an der
  beschriebenen oberen rechten Hakenspitze liegt.
- Detailtests sichern die neuen neutralen Parser-Koordinaten zusätzlich zu den
  bestehenden Gradient-/Renderer-Assertions ab.

## Artefakte

- `artifacts/converted_images/reports/DLG0021_plan_b_runSY_2026-06-26.log`

## Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_description_contract_helpers.py::test_description_parser_attaches_generic_checkbox_checkmark_geometry_ir tests/detailtests/test_description_contract_helpers.py::test_description_parser_attaches_dlg_style_checkbox_checkmark_geometry_ir tests/detailtests/test_description_contract_helpers.py::test_geometry_ir_renderer_emits_checkmark_stroke_gradient` läuft grün mit `3 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün und meldet weiterhin `0 occurrences`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-dlg-test2 --start DLG0021 --end DLG0021 --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m compileall -q src tests/detailtests/test_description_contract_helpers.py` läuft grün.

## Ergebnis

`DLG0021` bleibt auf dem katalogfreien Description-Geometry-IR-Pfad. Die
isolierte CLI-Metrik verbessert sich gegenüber Run SX von `Mean-Delta²=26451.279297`
auf `24805.169922` (`Fehler/Pixel=0.091186`), bleibt aber weiterhin oberhalb der
Review-Grenze. Das nächste Feintuning sollte die Haken-Konturstärke oder die
farbliche Registrierung weiter nachziehen oder auf `GE1410_L` rotieren.
