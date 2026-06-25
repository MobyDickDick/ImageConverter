# Nächstes Arbeitspaket – GE1410_L Diagramm-Dreieck-Primitive Run ST (2026-06-25)

Run ST bearbeitet nach Run SS den nächsten dokumentierten Plan-B-Kandidaten aus
`PLAN_B_KANDIDATEN.md`: `GE1410_L`. Der Kandidat war in der Run-SR-/Run-SS-
Triage als kompakter Diff-Fall mit generalisierten Kreis-/Linien-Seeds geführt,
benötigte aber für die konkrete Beschreibung einen generischen Diagrammvertrag.

## Änderungen

- Die katalogfreie Beschreibung eines kleinen Diagramms mit schwarzer x-/y-Achse,
  grauer horizontaler Referenzlinie sowie rotem oberem und blauem unterem Dreieck
  wird nun in eine description-driven Geometry-IR übersetzt.
- Der neue Vertrag nutzt ausschließlich generische Primitive: weißer Hintergrund,
  zwei schwarze Achsenlinien, graue horizontale Referenzlinie und zwei farbige
  `PolygonPath`-Dreiecke.
- Die Primitive-Zerlegung `chart_triangle_pair_decomposition_v1` dokumentiert die
  Achsen, die Referenzlinie und das obere/untere Dreieck als wiederverwendbaren
  Diagramm-/Dreieck-Contract.
- Zwei neutrale Detailtests sichern IR-Erzeugung und Dateinamen-Invarianz ohne
  Katalog- oder Bild-ID-Abhängigkeit ab.

## Artefakte

- `artifacts/converted_images/reports/GE1410_L_plan_b_runST_2026-06-25.log`

## Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_description_contract_helpers.py::test_description_parser_attaches_generic_chart_triangle_pair_geometry_ir tests/detailtests/test_description_contract_helpers.py::test_description_parser_chart_triangle_pair_geometry_ir_is_filename_invariant` läuft grün mit `2 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün und meldet weiterhin `0 occurrences`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ge1410-runst --start GE1410_L --end GE1410_L --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; der isolierte Run verbessert die Pixelmetrik deutlich auf `Mean-Delta²=3206.457520`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/review_conversion_quality.py --max-candidates 5` läuft grün; ohne Aktualisierung der allgemeinen Converted-SVG-Baseline bleibt die automatische Rotation weiterhin `DLG0021`, `GE1410_L`, `SE0041_1`, `GE9012_6M`, `GE9013_1M`.

## Ergebnis

`GE1410_L` besitzt nun einen katalogfreien, beschreibungsgetriebenen
Diagramm-/Dreieck-Primitive-Pfad. Gegenüber der Triage-Metrik
`Mean-Delta²=24170.253906` sinkt der isolierte echte Lauf auf `3206.457520`.
Die harte Pixelnähe-Grenze ist damit noch nicht erreicht, aber der Fall hängt
nun an einem neutralen Primitive-Contract statt an einer rein generischen
Rasterannäherung.
