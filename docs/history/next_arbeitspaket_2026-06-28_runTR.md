# Nächstes Arbeitspaket – GE1410_L generische PolygonPath-Stroke-Width-Probes Run TR (2026-06-28)

Run TR bleibt nach Run TQ beim zweitpriorisierten aktiven Plan-B-Kandidaten
`GE1410_L` aus `PLAN_B_KANDIDATEN.md`. Fokus ist kein Bild-ID-Sonderfall,
sondern ein kleines allgemeines Antialiasing-/Kontur-Feintuning für
`PolygonPath`-Primitive: Neben den relativen Stroke-Width-Probes werden nun auch
absolute, feinere Breiten-Nudges geprüft.

## Änderungen

- Die generische Geometry-IR-Elementoptimierung testet für `PolygonPath`-Elemente
  mit `stroke_width` zusätzlich die neutralen absoluten Breiten-Probes
  `stroke_width ± 0.01`.
- Die Probes werden wie alle vorhandenen Geometry-IR-Elementkandidaten nur dann
  übernommen, wenn der gerenderte Fehler strikt sinkt.
- Ein Detailtest sichert, dass die absoluten Breiten-Probes über den allgemeinen
  sequentiellen Optimierer auswählbar sind und nicht an eine konkrete Bild-ID
  gekoppelt werden.

## Perception-Lerneffekt

- `GE1410_L` bleibt `generalisiert`: Achsen-/Linien- und Dreieck-Seeds entstehen
  weiterhin aus dem beschreibungsbasierten Diagramm-/Dreieck-Primitive-Contract.
  Run TR erweitert nur die nachgelagerte, katalogfreie Elementregistrierung für
  antialiasing-sensitive `PolygonPath`-Konturen.

## Artefakte

- Isolierter Repro-Ausgabeordner: `/tmp/ic-ge1410-strokewidthprobe`

## Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py` läuft grün mit `15 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün und meldet weiterhin `0 occurrences`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ge1410-strokewidthprobe --start GE1410_L --end GE1410_L --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; die isolierte GE1410_L-Metrik bleibt gegenüber Run TQ stabil bei `Fehler/Pixel=0.010833` und `Mean-Delta²=777.012817`.

## Ergebnis

`GE1410_L` nutzt weiterhin denselben katalogfreien Description-Geometry-IR-Pfad.
Run TR erweitert die allgemeine Elementregistrierung um feine absolute
`PolygonPath`-Stroke-Width-Probes. Im isolierten GE1410_L-Einzellauf ergibt sich
keine zusätzliche Metrikverbesserung gegenüber Run TQ, aber der neue Suchschritt
steht katalogfrei für weitere antialiasing-sensitive PolygonPath-Fälle zur
Verfügung. Das nächste Paket kann in der aktiven Plan-B-Liste zu `SE0041_1`
rotieren oder weiteres Pixel-Feintuning für die verbleibenden Kandidaten
versuchen.
