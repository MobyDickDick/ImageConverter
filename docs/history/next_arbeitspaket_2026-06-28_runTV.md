# Nächstes Arbeitspaket – GE9012_6M generische RectBorder-Feinkanten-Probes Run TV (2026-06-28)

Run TV rotiert nach Run TU auf den aktiven BackBottom-Kandidaten `GE9012_6M`
aus `PLAN_B_KANDIDATEN.md`. Fokus ist kein neuer Bild-ID-Dispatch, sondern eine
kleine katalogfreie Erweiterung der allgemeinen Geometry-IR-Elementoptimierung:
Rechteck- und Farbfeldprimitive erhalten zusätzlich zu den bisherigen groben
Kantenverschiebungen feinere lokale BBox-Probes.

## Änderungen

- Die Standard-Candidate-Provider der sequentiellen Geometry-IR-Optimierung
  testen für `RectBorder` und `ColorPatch` nun neben ±0.02 auch ±0.01 pro
  BBox-Kante.
- Für andere Primitive bleibt die bisherige grobe BBox-Palette unverändert.
- Ein Detailtest sichert, dass ein `RectBorder` über die neue feine
  Kantenprobe tatsächlich ausgewählt werden kann, wenn nur diese Probe den
  Fehler senkt.

## Perception-Lerneffekt

- `GE9012_6M` bleibt `nur Sonderfall`: Die reine Bilddetektion liefert weiterhin
  keinen robusten BackBottom-/hellgraues-Quadrat-Seed. Der stabile Pfad bleibt
  der beschreibungsbasierte, katalogfreie `RectBorder`-Contract; Run TV macht
  dessen allgemeine Rechteckregistrierung jedoch feiner nutzbar.

## Artefakte

- Isolierter Repro-Ausgabeordner: `/tmp/ic-ge9012-runTV`

## Sicherung

- `pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py` läuft grün
  mit `16 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py`
  läuft grün und meldet weiterhin `0 occurrences`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ge9012-runTV --start GE9012_6M --end GE9012_6M --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order`
  läuft grün; die isolierte GE9012_6M-Metrik bleibt stabil bei
  `Fehler/Pixel=0.044122` und `Mean-Delta²=15386.639648`, weil keine feine
  Kantenprobe den bisherigen Farb-/BBox-Stand weiter verbessert.

## Ergebnis

`GE9012_6M` nutzt weiterhin denselben katalogfreien Description-Geometry-IR-Pfad.
Run TV erweitert die allgemeine Rechteck-/Farbfeldregistrierung um feinere
BBox-Kantenprobes; der konkrete Einzellauf bleibt metrisch stabil. Das nächste
Paket kann in der aktiven Plan-B-Liste weiterrotieren oder das verbleibende
BackBottom-/Diff-Feintuning fortsetzen.
