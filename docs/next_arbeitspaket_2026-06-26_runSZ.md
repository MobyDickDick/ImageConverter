# Nächstes Arbeitspaket – GE1410_L Diagramm-Dreieck-Feintuning Run SZ (2026-06-26)

Run SZ rotiert nach Run SY auf den in `PLAN_B_KANDIDATEN.md` dokumentierten
Folgekandidaten `GE1410_L`. Fokus ist das Pixel-Feintuning des bereits in Run ST
eingeführten katalogfreien Diagramm-/Dreieck-Primitive-Contracts.

## Änderungen

- Die oberen und unteren Dreieckspunkte wurden enger auf die im 25×25-Raster
  sichtbaren Dreieckskanten registriert: Basisbreite, Spitzenlage und vertikale
  Trennung folgen nun der beschriebenen Begegnung an der grauen Referenzlinie.
- Die Dreieckfarben und Konturstärke wurden an die gemessenen roten/blauen
  Füllflächen und die dunkle Kontur angepasst, ohne eine Bild-ID in den
  Runtime-Pfad einzuführen.
- Detailtests sichern die neutralen Parser-Koordinaten zusätzlich zur bestehenden
  Dateinamen-Invarianz des Diagramm-/Dreieck-Contracts ab.

## Artefakte

- Isolierter Repro-Ausgabeordner: `/tmp/ic-ge1410-after`

## Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_description_contract_helpers.py::test_description_parser_attaches_generic_chart_triangle_pair_geometry_ir tests/detailtests/test_description_contract_helpers.py::test_description_parser_chart_triangle_pair_geometry_ir_is_filename_invariant` läuft grün mit `2 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ge1410-after --start GE1410_L --end GE1410_L --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün.

## Ergebnis

`GE1410_L` bleibt auf dem katalogfreien Description-Geometry-IR-Pfad. Die
isolierte CLI-Metrik verbessert sich gegenüber Run ST/Run SY von
`Mean-Delta²=3206.457520` auf `1926.409546` (`Fehler/Pixel=0.016481`). Das
nächste Plan-B-Paket kann auf `SE0041_1` rotieren oder bei Bedarf weitere
Diagramm-Achsen-/Antialiasing-Feinheiten nachziehen.
