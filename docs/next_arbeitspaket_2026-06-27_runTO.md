# Nächstes Arbeitspaket – DLG0021 generische PolygonPath-Stroke-Probes Run TO (2026-06-27)

Run TO arbeitet nach Run TN erneut den höchstpriorisierten aktiven
Plan-B-Kandidaten `DLG0021` aus `PLAN_B_KANDIDATEN.md` ab. Fokus ist weiterhin
kein neuer Sonderfall, sondern eine kleine katalogfreie Erweiterung der
allgemeinen Geometry-IR-Elementoptimierung für farbnahe Polygonpfade.

## Änderungen

- Die generische Geometry-IR-Elementoptimierung testet für `PolygonPath`-Elemente
  nun zusätzlich eine neutrale Grau-/Grün-Stroke-Palette. Die Kandidaten werden
  wie alle anderen Element-Probes nur übernommen, wenn der gerenderte Fehler
  strikt sinkt.
- Damit können beschreibungsbasierte Haken-, Schatten- und ähnliche
  Kontrollpfad-Symbole ihre Konturfarbe lokal registrieren, ohne Bild-ID- oder
  Symbolfamilienlogik einzuführen.
- Ein Detailtest sichert, dass die neue Palette tatsächlich über den allgemeinen
  sequentiellen Optimierer auswählbar ist.

## Perception-Lerneffekt

- `DLG0021` bleibt `nur Sonderfall`: Die reine Bilddetektion liefert weiterhin
  keinen stabilen generischen Checkbox-/Checkmark-Seed. Der robuste Pfad bleibt
  der beschreibungsbasierte, katalogfreie Geometry-IR-Contract; Run TO macht
  dessen Elementregistrierung aber allgemeiner für farbnahe `PolygonPath`-
  Konturen nutzbar.

## Artefakte

- Isolierter Repro-Ausgabeordner: `/tmp/ic-dlg0021-strokeprobe`

## Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py` läuft grün mit `12 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün und meldet weiterhin `0 occurrences`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-dlg0021-strokeprobe --start DLG0021 --end DLG0021 --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; die isolierte DLG0021-Metrik bleibt stabil bei `Fehler/Pixel=0.081819` und `Mean-Delta²=18587.574219`, weil keine Stroke-Farbprobe den aktuellen Punkt-/Füllfarbstand weiter verbessert.

## Ergebnis

`DLG0021` nutzt weiterhin denselben katalogfreien Description-Geometry-IR-Pfad.
Run TO erweitert die allgemeine Elementregistrierung um neutrale Stroke-Farben;
der konkrete DLG0021-Einzellauf bleibt metrisch stabil. Das nächste Paket kann
in der aktiven Plan-B-Liste rotieren oder weiteres DLG-Farb-/Kontur-Feintuning
versuchen.
