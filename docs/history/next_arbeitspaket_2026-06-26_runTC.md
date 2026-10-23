# Nächstes Arbeitspaket – GE9013_1M BackBottom-Contract-Auswahl Run TC (2026-06-26)

Run TC arbeitet nach Run TB den dokumentierten Anschluss für den verbleibenden
BackBottom-/Light-Grey-Square-Kandidaten `GE9013_1M` aus `PLAN_B_KANDIDATEN.md`
ab. Ziel ist ein kleiner katalogfreier Auswahlschritt: Der bereits vorhandene
Description-Geometry-IR-Contract soll im Non-Composite-Pfad nicht mehr von der
allgemeinen elementweisen Rasterannäherung verdeckt werden.

## Änderungen

- Der semantische Non-Composite-Auswahlschritt erkennt nun neben Badge-/Checkmark-
  Semantik auch die neutrale Rolle `reference_light_grey_square` als bevorzugten
  Description-Geometry-IR-Contract.
- Der BackBottom-/`hellgraues Quadrat`-Pfad bleibt weiterhin rein
  beschreibungsgetrieben: Die Auswahl hängt an der neutralen IR-Rolle und nicht an
  einer GE9012- oder GE9013-spezifischen Bild-ID.
- Ein Regressionstest sichert, dass der BackBottom-Light-Grey-Square-Contract als
  semantischer Geometry-Kandidat bevorzugt wird und damit ausführbar bleibt.

## Perception-Lerneffekt

- `GE9013_1M`: weiterhin `nur Sonderfall`. Die Bilddetektion allein erzwingt noch
  keinen generischen Seed; der katalogfreie Beschreibungscontract wird aber nun
  auch in der Non-Composite-Kandidatenauswahl semantisch respektiert.

## Artefakte

- Isolierter Repro-Ausgabeordner: `/tmp/ic-ge9013-runTC`

## Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. pytest -q tests/test_image_composite_converter.py -k 'backbottom_square'` läuft grün mit `3 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün und meldet `0 occurrences`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ge9013-runTC --start GE9013_1M --end GE9013_1M --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; das Element-Validation-Log dokumentiert `status=non_composite_description_geometry_ir`, `non_composite_selection=semantic_description_geometry` und einen Description-Geometry-Kandidatenfehler von `46.570278`.

## Ergebnis

`GE9013_1M` nutzt den vorhandenen katalogfreien BackBottom-/Light-Grey-Square-
Contract nun tatsächlich als semantisch bevorzugten Non-Composite-Kandidaten. Der
vorherige Einzellauf blieb bei der elementweisen Annäherung mit Kandidatenfehler
`52.873611`; Run TC wählt stattdessen den Description-Geometry-IR-Pfad mit
`46.570278`. Damit ist die vertikale BackBottom-Variante nicht nur im Parser und
Renderer, sondern auch in der Runtime-Auswahl an den neutralen Primitive-Contract
gekoppelt.
