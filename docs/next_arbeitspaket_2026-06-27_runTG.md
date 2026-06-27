# Nächstes Arbeitspaket – GE1410_L Diagramm-Stroke-Feintuning Run TG (2026-06-27)

Run TG arbeitet nach Run TF den dokumentierten Anschluss aus
`docs/next_arbeitspaket_2026-06-26_runTF.md` ab und rotiert wieder auf
`GE1410_L` aus `PLAN_B_KANDIDATEN.md`. Fokus ist ein kleiner katalogfreier
Pixel-Refresh für den bereits generalisierten Diagramm-/Dreieck-Geometry-IR-
Contract.

## Änderungen

- Der neutrale Diagramm-/Dreieck-Contract bleibt ausschließlich an das
  Beschreibungsvokabular zu x-/y-Achse, grauer Referenzlinie sowie rotem oberem
  und blauem unterem Dreieck gekoppelt.
- Achsen und horizontale Referenzlinie wurden geringfügig verschlankt, damit die
  Rasterlinien weniger über die sichtbare 25×25-Kontur hinauslaufen.
- Die Dreieckskonturen wurden stärker verschlankt als die Achsenlinien, wodurch
  die farbigen Dreiecksflächen näher an der JPG-Rasterfüllung bleiben und die
  grauen Antialiasing-Säume reduziert werden.
- Detailtests sichern neben den neutralen Parser-Koordinaten nun auch die
  getrennten Stroke-Profile für Linien und Dreiecke ab.

## Perception-Lerneffekt

- `GE1410_L`: weiterhin `generalisiert`. Der Contract nutzt keine Katalog-ID,
  sondern generische Linien-/Polygon-Primitive aus der Beschreibung; Run TG ist
  nur ein Pixel-Feintuning der bereits generalisierten Primitive.

## Artefakte

- Isolierter Repro-Ausgabeordner: `/tmp/ic-ge1410-runTG`

## Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_description_contract_helpers.py::test_description_parser_attaches_generic_chart_triangle_pair_geometry_ir tests/detailtests/test_description_contract_helpers.py::test_description_parser_chart_triangle_pair_geometry_ir_is_filename_invariant` läuft grün mit `2 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün und meldet weiterhin `0 occurrences`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ge1410-runTG --start GE1410_L --end GE1410_L --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; der isolierte Kandidatenfehler sinkt auf `Mean-Delta²=1421.099243` und `Fehler/Pixel=0.013888`.

## Ergebnis

`GE1410_L` bleibt auf dem katalogfreien Description-Geometry-IR-Pfad. Das
Stroke-Feintuning verbessert die isolierte Pixelmetrik gegenüber Run SZ von
`Mean-Delta²=1926.409546` auf `1421.099243`, ohne neue Runtime-ID-Kopplung
einzuführen. Der nächste sinnvolle Schritt ist die Rotation zu `SE0041_1` oder
ein weiterer Qualitätsrefresh der aktiven Plan-B-Liste.
