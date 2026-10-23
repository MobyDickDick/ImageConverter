# Nächstes Arbeitspaket – DLG0021 generische PolygonPath-Opacity-Probes Run TY (2026-06-28)

Run TY arbeitet nach Run TP erneut den höchstpriorisierten aktiven
Plan-B-Kandidaten `DLG0021` aus `PLAN_B_KANDIDATEN.md` ab. Fokus bleibt ein
katalogfreier Ausbau der allgemeinen Geometry-IR-Elementoptimierung: weiche
Konturen und gefüllte Polygonpfade können nun über neutrale Opacity-Probes näher
an das Raster angepasst werden.

## Änderungen

- Die generische Geometry-IR-Elementoptimierung testet für `PolygonPath`-
  Elemente jetzt zusätzliche `stroke_opacity`- und `fill_opacity`-Probes.
- Die Probes sind bewusst neutral (`0.65`, `0.75`, `0.85`, `0.95`, `1.0`) und
  werden wie alle Elementkandidaten nur übernommen, wenn der gerenderte Fehler
  strikt sinkt.
- Der Geometry-IR-SVG-Renderer gibt optionale `stroke-opacity`- und
  `fill-opacity`-Attribute für `PolygonPath` aus; bei voller Deckkraft bleibt
  das bisherige SVG unverändert.
- Ein Detailtest sichert, dass die neue Opacity-Palette über den allgemeinen
  sequentiellen Optimierer ausgewählt werden kann.

## Perception-Lerneffekt

- `DLG0021` bleibt `nur Sonderfall`: Die reine Bilddetektion liefert weiterhin
  keinen stabilen generischen Checkbox-/Checkmark-Seed. Die Erweiterung ist aber
  nicht DLG-spezifisch, sondern verbessert den allgemeinen Element-Fit für
  Haken-, Schatten- und andere semitransparenznahe Polygonpfad-Symbole.

## Artefakte

- Isolierter Repro-Ausgabeordner: `/tmp/ic-dlg0021-opacityprobe`

## Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py` läuft grün mit `19 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-dlg0021-opacityprobe --start DLG0021 --end DLG0021 --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; die isolierte DLG0021-Metrik sinkt auf `Fehler/Pixel=0.077702` und `Mean-Delta²=17056.199219`.

## Ergebnis

`DLG0021` nutzt weiterhin denselben katalogfreien Description-Geometry-IR-Pfad.
Run TY erweitert die allgemeine Elementregistrierung um neutrale Opacity-Probes
und verbessert den isolierten Einzellauf gegenüber Run TP von
`Mean-Delta²=18587.574219` auf `17056.199219`.
