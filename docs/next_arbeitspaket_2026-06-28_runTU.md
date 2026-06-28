# Nächstes Arbeitspaket – SE0041_1 Square-Badge-Stem-Geometrie Run TU (2026-06-28)

Run TU rotiert nach `docs/next_arbeitspaket_2026-06-28_runTR.md` auf den
nächsten dokumentierten aktiven Plan-B-Kandidaten `SE0041_1` aus
`PLAN_B_KANDIDATEN.md`. Fokus ist kein Bild-ID-Sonderfall, sondern eine kleine
allgemeine Erweiterung des Square-Badge-Renderers: Der senkrechte Stem eines
viereckigen Badge-Kopfes kann nun optional aus neutralen Stem-Geometrieparametern
kommen, statt immer starr aus der Canvas-Breite abgeleitet zu werden.

## Änderungen

- `generateBadgeSvgImpl` behält für Square-Badges die bisherigen stabilen
  Default-Stem-Koordinaten bei, solange kein explizites Opt-in gesetzt ist.
- Mit `square_badge_use_explicit_stem_geometry=True` werden `stem_x`,
  `stem_top` und `stem_bottom` auch bei `head_style=square_badge` respektiert.
- Zwei Detailtests sichern sowohl das neue Opt-in als auch die unveränderten
  Legacy-Defaults gegen stale Kreis-Stem-Koordinaten ab.

## Perception-Lerneffekt

- `SE0041_1` bleibt `nur Sonderfall`: Die viereckige AC0811-Ableitung wird
  weiterhin über die beschreibungsbasierte Square-Badge-Semantik erzeugt. Run TU
  erweitert jedoch die katalogfreie Renderer-Schnittstelle, sodass künftige
  Raster-/Perception-Fits Stem-Lage und Stem-Länge eines Square-Badges neutral
  über Geometrieparameter nachführen können, ohne konkrete Bild-IDs oder feste
  SVG-Samples zu verwenden.

## Artefakte

- Isolierter Repro-Ausgabeordner: `/tmp/ic-se0041-squarestem2`

## Sicherung

- `pytest -q tests/detailtests/test_semantic_badge_svg_helpers.py tests/detailtests/test_semantic_badge_runtime_helpers.py` läuft grün mit `13 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-se0041-squarestem2 --start SE0041_1 --end SE0041_1 --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; die isolierte SE0041_1-Metrik bleibt stabil bei `Fehler/Pixel=0.01593158` und `Mean-Delta²=2436.707764`.

## Ergebnis

Run TU führt noch keine neue SE0041_1-Pixelverbesserung ein, beseitigt aber eine
Renderer-Einschränkung: Square-Badge-Stems können künftig katalogfrei aus
expliziten, gemessenen Geometrieparametern gerendert werden. Ohne Opt-in bleibt
existing Behavior stabil, sodass die aktuelle SE0041_1-Qualität nicht regressiert.
