# Nächstes Arbeitspaket – DLG0021 Checkmark-Gradient Run SX (2026-06-25)

Run SX arbeitet das nach Run SS offene Pixel-Feintuning für den aktiven
Plan-B-Kandidaten `DLG0021` weiter ab. Fokus ist die in der Beschreibung
explizit genannte Haken-Füllung mit grünem vertikalem Farbverlauf.

## Änderungen

- Der katalogfreie Checkbox-/Haken-Geometry-IR-Contract trägt für den grünen
  Haken jetzt ein deklaratives `stroke_gradient`-Metadatum mit dunklem oberen,
  mittlerem grünem und hellgrauem unteren Stop.
- Der generische `PolygonPath`-Renderer emittiert aus diesem Metadatum eine
  SVG-`linearGradient`-Definition und verwendet sie als Stroke-Füllung, ohne den
  Pfad an `DLG0021` oder eine andere Katalog-ID zu koppeln.
- Detailtests sichern sowohl die Parser-Metadaten als auch die konkrete
  SVG-Ausgabe des Gradienten ab.

## Artefakte

- `artifacts/converted_images/reports/DLG0021_plan_b_runSX_2026-06-25.log`

## Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_description_contract_helpers.py::test_description_parser_attaches_generic_checkbox_checkmark_geometry_ir tests/detailtests/test_description_contract_helpers.py::test_description_parser_attaches_dlg_style_checkbox_checkmark_geometry_ir tests/detailtests/test_description_contract_helpers.py::test_geometry_ir_renderer_emits_checkmark_stroke_gradient` läuft grün mit `3 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün und meldet weiterhin `0 occurrences`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-dlg0021-runsx --start DLG0021 --end DLG0021 --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; das Validierungslog protokolliert weiter `status=non_composite_description_geometry_ir` und `non_composite_selection=semantic_description_geometry`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m compileall -q src tests/detailtests/test_description_contract_helpers.py` läuft grün.

## Ergebnis

`DLG0021` bleibt auf dem katalogfreien Description-Geometry-IR-Pfad, der Haken
modelliert nun aber die beschriebene vertikale Farbcharakteristik statt eines
flachen grünen Strichs. Die isolierte CLI-Metrik bleibt mit
`Mean-Delta²=26451.279297` weiterhin klar oberhalb der Review-Grenze; das
nächste Feintuning sollte daher die Haken-/Checkbox-Geometrie und die
Rasterregistrierung weiter nachziehen.
