# Nächstes Arbeitspaket – SE0041_1 Square-Badge-Farbkontur Run TS (2026-06-28)

Run TS rotiert nach Run TR gemäß `PLAN_B_KANDIDATEN.md` zu `SE0041_1` zurück.
Fokus ist kein neuer Bild-ID-Dispatch, sondern ein kleines katalogfreies
Pixel-Feintuning des vorhandenen Square-Badge-Contracts: Der viereckige rote
Kopf nutzt nun eine gemessen nähere rote Füllfarbe und eine graue Kontur, passend
zur weiterhin neutralen Beschreibung „Viereck statt Kreis“.

## Änderungen

- Die Square-Badge-Variantenparameter wurden in einen kleinen neutralen Helper
  ausgelagert, damit Kopf-Farbe, graue Kontur, Canvas-Inset und Stem-Parameter
  direkt testbar sind.
- Der rote Square-Badge-Kopf rendert nicht mehr mit gesättigtem `#fc0200`,
  sondern mit dem rasterpassenderen `#e10821`.
- Die Kopfkontur rendert nun grau (`#a0a0a0`) statt rot; Stem-Farbe und
  Geometrie bleiben unverändert katalogfrei.
- Ein Regressionstest sichert die neutralen Square-Badge-Variantenparameter ohne
  konkrete Runtime-Bild-ID.

## Perception-Lerneffekt

- `SE0041_1` bleibt `nur Sonderfall`: Die stabile Seed-Quelle ist weiterhin die
  beschreibungsbasierte Square-Badge-Aliasableitung, nicht eine reine
  Bilddetektion. Run TS verbessert nur die generischen Farben/Konturparameter
  dieses katalogfreien Badge-Contracts.

## Artefakte

- Isolierter Repro-Ausgabeordner: `/tmp/ic-se0041-runTS`

## Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. pytest -q tests/test_image_composite_converter.py::test_square_badge_variant_params_use_neutral_red_head_with_grey_outline tests/test_image_composite_converter.py::test_generate_badge_svg_renders_square_badge_with_explicit_canvas_inset` läuft grün mit `2 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün und meldet weiterhin `0 occurrences`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-se0041-runTS --start SE0041_1 --end SE0041_1 --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; die isolierte `SE0041_1`-Metrik sinkt von `Mean-Delta²=3178.770264` auf `2436.707764`.

## Ergebnis

`SE0041_1` nutzt weiterhin den katalogfreien semantischen Square-Badge-Pfad.
Die Farb-/Konturregistrierung verbessert die isolierte Pixelmetrik sichtbar,
ohne neue Runtime-ID-Kopplung einzuführen. Das nächste Paket kann wieder in der
aktiven Plan-B-Liste rotieren oder weiteres Pixel-Feintuning für die
verbleibenden Kandidaten versuchen.
