# Nächstes Arbeitspaket – DLG0021 Checkmark-Lage-Feintuning Run TK (2026-06-27)

Run TK arbeitet nach Run TJ wieder den höchstpriorisierten aktiven
Plan-B-Kandidaten `DLG0021` aus `PLAN_B_KANDIDATEN.md` ab. Fokus ist ein
kleiner katalogfreier Pixel-Refresh innerhalb des vorhandenen
Checkbox-/Haken-Geometry-IR-Contracts.

## Änderungen

- Der Description-Geometry-IR-Contract bleibt ausschließlich an die neutrale
  Beschreibung „Haken vor Checkbox“ gekoppelt und führt keine neue Bild-ID-
  Verzweigung ein.
- Die Haken- und Schatten-Polyline wurde nochmals leicht nach links/oben
  verschoben, damit die Vektorkontur enger auf der sichtbaren Rasterspur sitzt.
- Die graue Schattenkontur wurde moderat verstärkt, während der grüne
  Gradientenstrich schmal bleibt; dadurch sinkt die harte Pixelmetrik im
  isolierten Einzellauf erneut.
- Die Detailtests sichern die neuen normalisierten Punkte und Stroke-Breiten für
  den neutralen DLG-Style-Checkbox-/Haken-Contract ab.

## Perception-Lerneffekt

- `DLG0021` bleibt `nur Sonderfall`: Die reine Bilddetektion liefert weiterhin
  keinen stabilen generischen Checkbox-/Checkmark-Seed. Der ausführbare Pfad ist
  weiterhin der beschreibungsbasierte, katalogfreie Geometry-IR-Contract mit
  `RectBorder` und `PolygonPath`-Haken.

## Artefakte

- Isolierter Repro-Ausgabeordner: `/tmp/ic-dlg0021-runTK`

## Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_description_contract_helpers.py::test_description_parser_attaches_dlg_style_checkbox_checkmark_geometry_ir tests/detailtests/test_description_contract_helpers.py::test_geometry_ir_renderer_emits_checkmark_stroke_gradient tests/detailtests/test_description_contract_helpers.py::test_description_parser_checkmark_geometry_ir_is_filename_invariant` läuft grün mit `3 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün und meldet weiterhin `0 occurrences`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-dlg0021-runTK --start DLG0021 --end DLG0021 --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; `Mean-Delta²` sinkt von Run TH `23650.539062` auf `21642.482422`.

## Ergebnis

`DLG0021` nutzt weiterhin denselben katalogfreien Description-Geometry-IR-Pfad,
rendert den Haken aber nochmals lage- und schattenseitig näher am
Referenzraster. Das nächste Paket kann entweder weiteres Farb-/Kontur-Feintuning
für `DLG0021` versuchen oder wieder in der aktiven Plan-B-Liste rotieren.
