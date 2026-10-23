# Nächstes Arbeitspaket – GE1001_M Checkmark-Primitive Run SQ (2026-06-24)

Run SQ arbeitet nach Run SP den dort benannten nächsten konkreten Umsetzungsschritt ab: Die katalogfreie GE1001-Beschreibung wird in einen generischen Haken-/Checkmark-Primitive-Contract übersetzt.

## Änderungen

- `buildGeometryIrFromDescriptionImpl(...)` erkennt jetzt allgemeine Beschreibungen eines grünen Hakens beziehungsweise Checkmarks mit schrägen Schenkeln, ohne Bild- oder Katalog-ID zu verwenden.
- Der neue Geometry-IR-Vertrag besteht aus weißem `ColorPatch`, grauer Schatten-/Konturlinie und grüner `PolygonPath`-Hakenlinie mit expliziter Primitive-Zerlegung in zwei Schenkel plus Außenkontur.
- Der generische `PolygonPath`-Renderer berücksichtigt nun deklarierte `linecap`- und `linejoin`-Attribute, damit dicke offene Hakenlinien nicht mehr mit abgeschnittenen Enden gerendert werden.
- Regressionstests sichern sowohl die Checkmark-IR-Erzeugung als auch Dateinamen-Invarianz mit neutralen, katalogfremden Namen.

## Artefakte

- `artifacts/converted_images/reports/GE1001_M_plan_b_runSQ_2026-06-24.log`

## Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_description_contract_helpers.py::test_description_parser_attaches_generic_checkmark_geometry_ir tests/detailtests/test_description_contract_helpers.py::test_description_parser_checkmark_geometry_ir_is_filename_invariant` läuft grün.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün und meldet weiterhin `0 occurrences`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_description_contract_helpers.py` läuft grün.
- `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ge1001-runsq --start GE1001_M --end GE1001_M --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün und erzeugt eine SVG-Ausgabe mit `checkmark_background`, `checkmark_shadow_outline` und `checkmark_green_stroke`.

## Ergebnis

Der in Run SP dokumentierte fachliche Blocker ist technisch adressiert: `GE1001_M` wird nicht mehr nur über die präzisere Beschreibung triagiert, sondern erhält einen katalogfreien Checkmark-Geometry-IR-Seed. Die Qualitätsmetrik verbessert sich leicht von `Mean-Delta²=18208.144531` auf `17899.730469`; wegen verbleibender Pixel-/Perception-Abweichungen bleibt der Fall aber als Qualitätskandidat beobachtungswürdig.
