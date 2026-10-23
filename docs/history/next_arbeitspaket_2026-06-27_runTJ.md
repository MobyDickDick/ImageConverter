# Nächstes Arbeitspaket – GE1410_L Diagramm-Contract-Absicherung Run TJ (2026-06-27)

Run TJ rotiert nach Run TH wieder auf den dokumentierten Plan-B-Kandidaten
`GE1410_L` aus `PLAN_B_KANDIDATEN.md`. Fokus ist kein neuer Bild-ID-Dispatch,
sondern eine kleine Absicherung des bereits pixelnäher getunten, katalogfreien
Diagramm-/Dreieck-Contracts: Die im 25×25-Raster kalibrierten Achsen-,
Referenzlinien- und Dreieck-SVG-Koordinaten sollen als ausführbarer
Renderer-Contract festgehalten werden.

## Änderungen

- Der bestehende Beschreibungspfad für Diagramm mit schwarzer x-/y-Achse,
  grauer horizontaler Referenzlinie sowie rotem oberem und blauem unterem
  Dreieck bleibt unverändert katalogfrei.
- Ein zusätzlicher Detailtest rendert den neutralen Geometry-IR-Contract auf
  25×25 Pixel und sichert die kalibrierten SVG-Pfade, Stroke-Breiten und
  Füllfarben für Achsen, Referenzlinie und beide Dreiecke ab.
- Damit ist das bisherige GE1410-Feintuning nicht nur im Parser, sondern auch im
  finalen Geometry-IR-SVG-Renderer gegen versehentliche Regressionen geschützt.

## Perception-Lerneffekt

- `GE1410_L`: weiterhin `generalisiert`. Der Contract hängt an Diagramm-,
  Achsen-, Horizontalreferenz- und Dreieck-Vokabular und nicht an einer
  GE1410-spezifischen Runtime-Regel.

## Artefakte

- Isolierter Repro-Ausgabeordner: `/tmp/ic-ge1410-runTJ`

## Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_description_contract_helpers.py::test_description_parser_attaches_generic_chart_triangle_pair_geometry_ir tests/detailtests/test_description_contract_helpers.py::test_geometry_ir_renderer_emits_chart_triangle_pair_calibrated_svg tests/detailtests/test_description_contract_helpers.py::test_description_parser_chart_triangle_pair_geometry_ir_is_filename_invariant` läuft grün mit `3 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün und meldet weiterhin `0 occurrences`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ge1410-runTJ --start GE1410_L --end GE1410_L --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; die isolierte Metrik bleibt bei `Mean-Delta²=1421.099243`.

## Ergebnis

Das nächste dokumentierte Arbeitspaket ist als Regression-Guard für den
GE1410-Diagramm-Contract abgeschlossen. Die Pixelmetrik bleibt stabil auf dem
zuletzt erreichten Niveau, und spätere Antialiasing-/Geometrie-Experimente
müssen die katalogfreie Renderer-Signatur nun explizit aktualisieren, statt sie
unbemerkt zu verschieben.
