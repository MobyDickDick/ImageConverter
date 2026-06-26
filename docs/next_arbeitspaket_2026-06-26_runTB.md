# Nächstes Arbeitspaket – GE9012_6M BackBottom-Light-Grey-Tuning Run TB (2026-06-26)

Run TB arbeitet nach Run TA den dokumentierten Anschluss aus
`docs/next_arbeitspaket_2026-06-26_runTA.md` ab und rotiert auf
`GE9012_6M` aus `PLAN_B_KANDIDATEN.md`. Ziel ist ein kleiner, katalogfreier
Feintuning-Schritt am bereits in Run SV eingeführten BackBottom-/hellgraues-
Quadrat-Contract.

## Änderungen

- Der BackBottom-/`hellgraues Quadrat`-Description-Contract bleibt ein
  vollflächiger `RectBorder` mit `light_grey_square_decomposition_v1`, nutzt
  aber nun ein helleres neutrales Grau (`#e8e8e8`) statt des bisherigen
  dunkleren Default-Rechteckgraus.
- Die Auswahl hängt weiterhin ausschließlich am Beschreibungsvokabular
  `BackBottom` beziehungsweise `hellgraues Quadrat`; es wurde keine GE9012- oder
  GE9013-spezifische Runtime-Regel ergänzt.
- Die bestehenden Regressionstests wurden auf das hellere BackBottom-Grau für
  breite und vertikale Canvas-Varianten aktualisiert.

## Perception-Lerneffekt

- `GE9012_6M`: weiterhin `nur Sonderfall`. Die reine Bilddetektion erzwingt
  noch keinen generischen Seed, aber der beschreibungsbasierte Light-Grey-Square-
  Contract ist katalogfrei und skaliert über die Canvas-Abmessungen.

## Artefakte

- Isolierter Repro-Ausgabeordner: `/tmp/ic-ge9012-6m-runTB`
- Familien-Repro-Ausgabeordner: `/tmp/ic-ge9012-runTB`

## Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. pytest -q tests/test_image_composite_converter.py -k 'backbottom_square'` läuft grün mit `2 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün und meldet `0 occurrences`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ge9012-6m-runTB --start GE9012_6M --end GE9012_6M --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün.

## Ergebnis

Das nächste dokumentierte Arbeitspaket ist als kleiner katalogfreier
BackBottom-Farbabgleich abgeschlossen. Der semantische Contract repräsentiert
„hellgraues Quadrat“ nun näher an den hellen Rasterzentren der aktiven
BackBottom-Varianten, ohne Bild-ID-Wissen in `src/` einzuführen. Der echte
`GE9012_6M`-Einzellauf wählt weiterhin die elementweise Plan-B-Annäherung als
pixelnähere Variante; weiteres Pixel-Feintuning an Antialiasing oder
Bild-/Beschreibung-Fusion bleibt daher offen.
