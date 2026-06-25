# Nächstes Arbeitspaket – DLG0021 Checkbox-Checkmark-Primitive Run SS (2026-06-25)

Run SS bearbeitet nach Run SR den nächsten dokumentierten Plan-B-Kandidaten aus
`PLAN_B_KANDIDATEN.md`: `DLG0021`. Der Kandidat war in der Run-SR-Triage als
kompakter Diff-Fall mit noch nicht erkanntem Perception-Lerneffekt geführt.

## Änderungen

- Die vorhandene katalogfreie Haken-/Checkbox-Beschreibung wird nun im
  Non-Composite-Pfad tatsächlich als beschreibungsgetriebene Geometry-IR
  zugelassen: `PolygonPath` gehört jetzt zu den description-driven Primitive-
  Arten.
- Checkmark-Geometry-IR wird bei der Kandidatenauswahl als semantischer
  Beschreibungskandidat priorisiert, sodass der Algorithmus nicht mehr auf die
  rein elementweise Rasterannäherung zurückfällt.
- Ein neutraler Detailtest sichert die DLG-artige Kurzbeschreibung ohne
  Dateinamen- oder Katalog-ID-Abhängigkeit ab.

## Artefakte

- `artifacts/converted_images/reports/DLG0021_plan_b_runSS_2026-06-25.log`

## Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_description_contract_helpers.py::test_description_parser_attaches_dlg_style_checkbox_checkmark_geometry_ir tests/detailtests/test_description_contract_helpers.py::test_description_parser_attaches_generic_checkbox_checkmark_geometry_ir` läuft grün mit `2 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün und meldet weiterhin `0 occurrences`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-dlg0021-runss --start DLG0021 --end DLG0021 --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; das Validierungslog protokolliert `status=non_composite_description_geometry_ir` und `non_composite_selection=semantic_description_geometry`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/review_conversion_quality.py --max-candidates 5` läuft grün; ohne Aktualisierung der allgemeinen Converted-SVG-Baseline bleibt die automatische Rotation weiterhin `DLG0021`, `GE1410_L`, `SE0041_1`, `GE9012_6M`, `GE9013_1M`.

## Ergebnis

`DLG0021` besitzt nun einen katalogfreien, beschreibungsgetriebenen
Checkbox-/Haken-Primitive-Pfad. Der reale CLI-Pfad rendert die semantische
Geometry-IR und dokumentiert alle drei Kandidatenfehler
(Perception-Seed, Description-IR, Element-Fit). Die Pixelmetrik im isolierten
Run bleibt sichtbar hoch (`Mean-Delta²=22598.726562`), verbessert sich aber
gegenüber der Run-SR-Triage (`24856.818359`) und ist nun an einen neutralen
Primitive-Contract statt an den Raster-Fallback gebunden.
