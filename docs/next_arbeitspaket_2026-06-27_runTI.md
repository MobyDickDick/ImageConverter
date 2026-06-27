# Nächstes Arbeitspaket – SE0041_1 Square-Badge-Inset-Feintuning Run TI (2026-06-27)

Run TI rotiert nach Run TG auf den dokumentierten Anschluss `SE0041_1` aus
`PLAN_B_KANDIDATEN.md`. Fokus ist ein katalogfreier Pixel-Refresh für den bereits
als Sonderfall dokumentierten Square-Badge-Seed aus der AC0811-Aliasbeschreibung.

## Änderungen

- Der semantische Square-Badge-Pfad bleibt an das Beschreibungsvokabular
  „viereckig anstatt rund“ gekoppelt und erbt weiterhin nur die neutrale
  AC0811-Badge-Struktur.
- Full-Canvas-Square-Badges können nun explizite, gemessene Inset- und
  Höhenparameter tragen, ohne eine Katalog-ID in den SVG-Renderer einzuführen.
- `SE0041_1` nutzt diese neutralen Inset-Parameter für die rote Kopfkachel: Der
  Kopf beginnt pixelnäher innerhalb des 28×44-Rasters und die vertikale rote
  Kachelhöhe folgt der JPG-Kante enger.
- Ein Detailtest sichert die neue explizite Inset-/Höhensteuerung zusätzlich zur
  bestehenden Full-Canvas-Farbabsicherung ab.

## Perception-Lerneffekt

- `SE0041_1`: weiterhin `nur Sonderfall`. Die reine Bilddetektion liefert keinen
  stabilen generischen Seed; der robuste Pfad bleibt der beschreibungsbasierte,
  katalogfreie Square-Badge-Contract.

## Artefakte

- Isolierter Repro-Ausgabeordner: `/tmp/ic-se0041-runTI`

## Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/test_image_composite_converter.py::test_generate_badge_svg_renders_square_badge_head_with_explicit_colors tests/test_image_composite_converter.py::test_generate_badge_svg_renders_square_badge_with_explicit_canvas_inset` läuft grün mit `2 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-se0041-runTI --start SE0041_1 --end SE0041_1 --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; der isolierte Kandidatenfehler sinkt auf `Mean-Delta²=3178.770264` und `Fehler/Pixel=0.015960`.

## Ergebnis

`SE0041_1` bleibt auf dem katalogfreien semantischen Square-Badge-Pfad. Das
Inset-/Höhen-Feintuning verbessert die isolierte Pixelmetrik gegenüber Run TE von
`Mean-Delta²=7242.835938` auf `3178.770264`, ohne neue Runtime-ID-Kopplung
einzuführen. Der nächste sinnvolle Schritt ist die Rotation zu `GE9012_6M` oder
ein weiterer Qualitätsrefresh der aktiven Plan-B-Liste.
