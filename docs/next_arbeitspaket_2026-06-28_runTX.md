# Nächstes Arbeitspaket – GE9013_1M generische RectBorder-Stroke-Probes Run TX (2026-06-28)

Run TX rotiert nach Run TW auf den aktiven BackBottom-Variantenkandidaten
`GE9013_1M` aus `PLAN_B_KANDIDATEN.md`. Fokus ist kein neuer Bild-ID-Dispatch,
sondern eine kleine katalogfreie Erweiterung der allgemeinen Geometry-IR-
Elementoptimierung: Rechteckrahmen können ihre neutrale Konturfarbe lokal
nachregistrieren.

## Änderungen

- Der Standard-Candidate-Provider der sequentiellen Geometry-IR-Optimierung
  testet für `RectBorder`-Elemente mit gesetzter Kontur nun eine neutrale
  Graupalette von dunkler bis heller Rahmenfarbe.
- Die Kandidaten werden wie alle anderen Geometry-IR-Elementprobes nur
  übernommen, wenn der gerenderte Fehler strikt sinkt.
- Ein Detailtest sichert, dass die neue `RectBorder`-Stroke-Palette über den
  allgemeinen sequentiellen Optimierer auswählbar ist und nicht an konkrete
  Bild-IDs gekoppelt wird.

## Perception-Lerneffekt

- `GE9013_1M` bleibt `nur Sonderfall`: Die reine Bilddetektion liefert weiterhin
  keinen robusten BackBottom-/hellgraues-Quadrat-Seed. Der stabile Pfad bleibt
  der beschreibungsbasierte, katalogfreie `RectBorder`-/`ColorPatch`-Contract;
  Run TX macht dessen allgemeine Rahmenfarbregistrierung jedoch auch für
  schmale/vertikale BackBottom-Varianten nutzbar.

## Artefakte

- Isolierter Repro-Ausgabeordner: `/tmp/ic-ge9013-runTX`

## Sicherung

- `pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py` läuft grün
  mit `18 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py`
  läuft grün und meldet weiterhin `0 occurrences`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ge9013-runTX --start GE9013_1M --end GE9013_1M --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order`
  läuft grün; die isolierte GE9013_1M-Metrik bleibt gegenüber Run TM stabil bei
  `Fehler/Pixel=0.035766` und `Mean-Delta²=12989.524414`, weil keine neutrale
  Rahmenfarbprobe den bisherigen Farb-/Geometriestand weiter verbessert.

## Ergebnis

`GE9013_1M` nutzt weiterhin denselben katalogfreien Description-Geometry-IR-Pfad.
Run TX erweitert die allgemeine Rechteckrahmenregistrierung um neutrale
Stroke-Farbprobes; der konkrete Einzellauf bleibt metrisch stabil. Das nächste
Paket kann in der aktiven Plan-B-Liste weiterrotieren oder das verbleibende
BackBottom-/Diff-Feintuning fortsetzen.
