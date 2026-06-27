# Nächstes Arbeitspaket – DLG0021 generische PolygonPath-Linecap-Probes Run TP (2026-06-27)

Run TP arbeitet nach Run TO erneut den höchstpriorisierten aktiven
Plan-B-Kandidaten `DLG0021` aus `PLAN_B_KANDIDATEN.md` ab. Fokus ist weiterhin
kein neuer Sonderfall, sondern eine kleine katalogfreie Erweiterung der
allgemeinen Geometry-IR-Elementoptimierung für Polygonpfade mit konturabhängigen
End- und Eckstilen.

## Änderungen

- Die generische Geometry-IR-Elementoptimierung testet für `PolygonPath`-Elemente
  nun zusätzlich neutrale `linecap`-Probes (`butt`, `round`, `square`) und
  `linejoin`-Probes (`round`, `miter`, `bevel`).
- Die Kandidaten werden wie alle anderen Element-Probes nur übernommen, wenn der
  gerenderte Fehler strikt sinkt. Dadurch bleiben vorhandene DLG-Parameter
  stabil, während ähnliche Haken-, Schatten- und Kontrollpfad-Symbole ihre
  Konturabschlüsse katalogfrei registrieren können.
- Ein Detailtest sichert, dass die neue Linecap-/Linejoin-Palette tatsächlich
  über den allgemeinen sequentiellen Optimierer auswählbar ist.

## Perception-Lerneffekt

- `DLG0021` bleibt `nur Sonderfall`: Die reine Bilddetektion liefert weiterhin
  keinen stabilen generischen Checkbox-/Checkmark-Seed. Der robuste Pfad bleibt
  der beschreibungsbasierte, katalogfreie Geometry-IR-Contract; Run TP macht
  dessen Elementregistrierung aber allgemeiner für konturnahe `PolygonPath`-
  End- und Eckstile nutzbar.

## Artefakte

- Isolierter Repro-Ausgabeordner: `/tmp/ic-dlg0021-linecapprobe`

## Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py` läuft grün mit `13 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün und meldet weiterhin `0 occurrences`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-dlg0021-linecapprobe --start DLG0021 --end DLG0021 --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; die isolierte DLG0021-Metrik bleibt stabil bei `Fehler/Pixel=0.081819` und `Mean-Delta²=18587.574219`, weil keine Linecap-/Linejoin-Probe den aktuellen Punkt-/Farbstand weiter verbessert.

## Ergebnis

`DLG0021` nutzt weiterhin denselben katalogfreien Description-Geometry-IR-Pfad.
Run TP erweitert die allgemeine Elementregistrierung um neutrale Konturabschluss-
und Eckstil-Probes; der konkrete DLG0021-Einzellauf bleibt metrisch stabil. Das
nächste Paket kann in der aktiven Plan-B-Liste rotieren oder weiteres
DLG-Farb-/Kontur-Feintuning versuchen.
