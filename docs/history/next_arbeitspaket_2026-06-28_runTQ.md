# Nächstes Arbeitspaket – GE1410_L generische PolygonPath-Füllfarb-Probes Run TQ (2026-06-28)

Run TQ rotiert nach dem DLG0021-Konturpaket auf den zweitpriorisierten aktiven
Plan-B-Kandidaten `GE1410_L` aus `PLAN_B_KANDIDATEN.md`. Fokus ist weiterhin
kein neuer Bild-ID-Sonderfall, sondern eine kleine katalogfreie Erweiterung der
allgemeinen Geometry-IR-Elementoptimierung für gefüllte `PolygonPath`-Primitive
wie Diagramm-Dreiecke.

## Änderungen

- Die generische Geometry-IR-Elementoptimierung testet für `PolygonPath`-Elemente
  mit echter Füllung nun zusätzlich eine kleine neutrale Rot-/Blau-Palette.
- Die neuen Füllfarb-Kandidaten werden wie die vorhandenen Punkt-, Stroke-,
  Linecap- und Linejoin-Probes nur übernommen, wenn der gerenderte Fehler strikt
  sinkt.
- Ein Detailtest sichert, dass die Palette über den allgemeinen sequentiellen
  Optimierer auswählbar ist und nicht an eine konkrete Bild-ID gekoppelt wird.

## Perception-Lerneffekt

- `GE1410_L` bleibt `generalisiert`: Achsen-/Linien- und Dreieck-Seeds entstehen
  weiterhin aus dem beschreibungsbasierten Diagramm-/Dreieck-Primitive-Contract.
  Run TQ macht die nachgelagerte Elementregistrierung allgemeiner für gefüllte
  rote und blaue `PolygonPath`-Primitive nutzbar.

## Artefakte

- Isolierter Repro-Ausgabeordner: `/tmp/ic-ge1410-polygonfillprobe`

## Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py` läuft grün mit `14 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün und meldet weiterhin `0 occurrences`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ge1410-polygonfillprobe --start GE1410_L --end GE1410_L --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; die isolierte GE1410_L-Metrik verbessert sich auf `Fehler/Pixel=0.010833` und `Mean-Delta²=777.012817`.

## Ergebnis

`GE1410_L` nutzt weiterhin denselben katalogfreien Description-Geometry-IR-Pfad.
Run TQ erweitert die allgemeine Elementregistrierung um neutrale Rot-/Blau-
Füllfarb-Probes für gefüllte `PolygonPath`-Elemente und senkt den isolierten
GE1410_L-Einzellauf von zuletzt `Mean-Delta²=1421.099243` auf `777.012817`.
Das nächste Paket kann in der aktiven Plan-B-Liste weiter rotieren oder weiteres
Antialiasing-/Pixel-Feintuning für die verbleibenden Kandidaten versuchen.
