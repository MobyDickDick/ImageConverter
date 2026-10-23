# Nächstes Arbeitspaket – GE9012_6M BackBottom-Farbregistrierung Run TL (2026-06-27)

Run TL rotiert nach Run TK auf den aktiven Plan-B-Kandidaten `GE9012_6M` aus
`PLAN_B_KANDIDATEN.md`. Fokus ist ein kleiner katalogfreier Pixel-Refresh für
den vorhandenen BackBottom-/hellgraues-Quadrat-Geometry-IR-Contract.

## Änderungen

- Der BackBottom-Contract bleibt weiterhin an die neutrale Beschreibung
  „hellgraues Quadrat“ gekoppelt und führt keine neue Bild-ID-Verzweigung ein.
- Die generische Geometry-IR-Elementoptimierung prüft nun bei `RectBorder`- und
  `ColorPatch`-Elementen zusätzlich neutrale helle Füllfarb-Proben. Dadurch kann
  ein beschriebenes hellgraues Rechteck seine Rasterfarbe lokal verbessern,
  ohne die dokumentierte Ausgangs-IR oder Kataloglogik zu verändern.
- Die bestehende globale Rasterregistrierung nutzt diese elementweise
  Nachregistrierung nach der Lage-/Skalenoptimierung mit; nur strikt bessere
  Kandidaten werden übernommen.
- Ein Detailtest sichert, dass die Default-Elementoptimierung eine bessere
  neutrale Rechteckfüllfarbe akzeptiert.

## Perception-Lerneffekt

- `GE9012_6M` bleibt `nur Sonderfall`: Die reine Bilddetektion ist weiterhin
  nicht der primäre stabile Pfad. Der ausführbare Pfad ist der
  beschreibungsbasierte, katalogfreie BackBottom-/hellgraues-Quadrat-Contract,
  jetzt mit neutraler Farb-Feinregistrierung.

## Artefakte

- Isolierter Repro-Ausgabeordner: `/tmp/ic-ge9012-runTL`

## Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py tests/test_image_composite_converter.py::test_backbottom_square_description_builds_catalog_free_rect_ir tests/test_image_composite_converter.py::test_backbottom_square_description_is_preferred_semantic_geometry_candidate` läuft grün mit `10 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün und meldet weiterhin `0 occurrences`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ge9012-runTL --start GE9012_6M --end GE9012_6M --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; `Mean-Delta²` sinkt vom lokalen Vorlauf `22544.404297` auf `15386.639648`.

## Ergebnis

`GE9012_6M` nutzt weiterhin denselben katalogfreien Description-Geometry-IR-Pfad,
rendert den BackBottom-Füllton aber nach der neutralen Elementregistrierung
pixelnäher. Das nächste Paket kann wieder in der aktiven Plan-B-Liste rotieren
oder das verbleibende BackBottom-/Diff-Feintuning fortsetzen.
