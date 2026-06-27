# Nächstes Arbeitspaket – DLG0021 generische Geometry-IR-Elementverfeinerung Run TN (2026-06-27)

Run TN arbeitet nach Run TM wieder den höchstpriorisierten aktiven
Plan-B-Kandidaten `DLG0021` aus `PLAN_B_KANDIDATEN.md` ab. Fokus ist kein neuer
Sonderfall, sondern eine kleine katalogfreie Erweiterung der allgemeinen
Geometry-IR-Elementoptimierung für farb- und punktnahe Polylines.

## Änderungen

- Die generische Geometry-IR-Elementoptimierung kennt nun zusätzlich helle,
  grünstichige Füllfarb-Probes für `ColorPatch`-/`RectBorder`-Elemente. Diese
  Palette ist neutral und wird nur übernommen, wenn der Renderfehler sinkt.
- `PolygonPath`-Elemente erhalten lokale Punkt-Probes je Kontrollpunkt und
  Koordinate. Dadurch kann ein beschreibungsbasierter Hakenpfad seine
  normierten Stützpunkte in kleinen Schritten an das Raster annähern, ohne
  neue Bild-ID- oder Symbol-Familienlogik einzuführen.
- Detailtests sichern sowohl die neue grünstichige Füllfarb-Registrierung als
  auch die lokale `PolygonPath`-Punktverfeinerung ab.

## Perception-Lerneffekt

- `DLG0021` bleibt `nur Sonderfall`: Die reine Bilddetektion liefert weiterhin
  keinen stabilen generischen Checkbox-/Checkmark-Seed. Der robuste Pfad bleibt
  der beschreibungsbasierte, katalogfreie Geometry-IR-Contract; Run TN macht
  dessen Elementregistrierung aber allgemeiner für ähnliche grünstichige
  Kontrollpfad-Symbole nutzbar.

## Artefakte

- Isolierter Repro-Ausgabeordner: `/tmp/ic-dlg0021-pointprobe`

## Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py tests/detailtests/test_description_contract_helpers.py::test_description_parser_attaches_dlg_style_checkbox_checkmark_geometry_ir tests/detailtests/test_description_contract_helpers.py::test_geometry_ir_renderer_emits_checkmark_stroke_gradient tests/detailtests/test_description_contract_helpers.py::test_description_parser_checkmark_geometry_ir_is_filename_invariant` läuft grün mit `14 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün und meldet weiterhin `0 occurrences`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-dlg0021-pointprobe --start DLG0021 --end DLG0021 --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; der isolierte Kandidatenfehler sinkt von `47.703125` auf `47.174769`, und `Mean-Delta²` sinkt von `18762.619141` auf `18587.574219`.

## Ergebnis

`DLG0021` nutzt weiterhin denselben katalogfreien Description-Geometry-IR-Pfad,
rendert den Haken aber durch allgemeine `PolygonPath`-Punktprobes und neutrale
Füllfarb-Probes etwas pixelnäher. Das nächste Paket kann in der aktiven
Plan-B-Liste rotieren oder weiteres DLG-Farb-/Kontur-Feintuning versuchen.
