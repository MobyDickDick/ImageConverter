# Nächstes Arbeitspaket – DLG0021 Checkmark-Lage-/Schatten-Refresh Run TH (2026-06-26)

Run TH setzt nach Run TF das nächste dokumentierte Feintuning für den weiterhin
höchstpriorisierten Plan-B-Kandidaten `DLG0021` aus `PLAN_B_KANDIDATEN.md` um.
Ziel ist ein kleiner katalogfreier Pixel-Refresh innerhalb des vorhandenen
Checkbox-/Haken-Geometry-IR-Contracts.

## Änderungen

- Der Description-Geometry-IR-Contract bleibt ausschließlich an die neutrale
  Beschreibung „Haken vor Checkbox“ gekoppelt und führt keine neue Bild-ID-
  Verzweigung ein.
- Die Haken- und Schatten-Polyline wurde leicht nach links/oben verschoben, damit
  der gerenderte Haken näher an der sichtbaren Rasterkontur sitzt.
- Die graue Schattenkontur wurde gegenüber Run TF etwas verstärkt, während der
  grüne Gradientenstrich schmaler bleibt; dadurch sinkt die harte Pixelmetrik im
  isolierten Einzellauf erneut.
- Der bestehende Contract-Test wurde auf die neuen normalisierten Punkte und
  Stroke-Widths aktualisiert.

## Perception-Lerneffekt

- `DLG0021` bleibt `nur Sonderfall`: Die reine Bilddetektion liefert weiterhin
  keinen stabilen generischen Checkbox-/Checkmark-Seed. Der ausführbare Pfad ist
  weiterhin der beschreibungsbasierte, katalogfreie Geometry-IR-Contract mit
  `RectBorder` und `PolygonPath`-Haken.

## Artefakte

- Isolierter Repro-Ausgabeordner: `/tmp/ic-dlg0021-runTH`

## Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_description_contract_helpers.py::test_description_parser_attaches_dlg_style_checkbox_checkmark_geometry_ir tests/detailtests/test_description_contract_helpers.py::test_geometry_ir_renderer_emits_checkmark_stroke_gradient` läuft grün mit `2 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-dlg0021-runTH --start DLG0021 --end DLG0021 --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; `Mean-Delta²` sinkt von Run TF `24454.230469` auf `23650.539062`.

## Ergebnis

`DLG0021` nutzt weiterhin denselben katalogfreien Description-Geometry-IR-Pfad,
rendert den Haken aber lage- und schattenseitig näher am Referenzraster. Das
nächste Paket kann entweder weiteres Farb-/Kontur-Feintuning für `DLG0021`
versuchen oder wieder auf `GE1410_L` rotieren.
