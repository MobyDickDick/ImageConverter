# Nächstes Arbeitspaket – DLG0021 Checkmark-Stroke-Feintuning Run TF (2026-06-26)

Run TF arbeitet nach dem Run-TD-Refresh wieder den höchstpriorisierten aktiven
Plan-B-Kandidaten `DLG0021` aus `PLAN_B_KANDIDATEN.md` ab. Fokus ist ein kleiner,
katalogfreier Pixel-Refresh für die bereits dokumentierte Checkbox-/Haken-
Geometry-IR.

## Änderungen

- Der neutrale Description-Geometry-IR-Contract bleibt unverändert an die
  Beschreibung „Haken vor Checkbox“ gekoppelt und nicht an eine Katalog-ID.
- Die Hakenkontur wurde geringfügig verschlankt: Schattenkontur und grüner
  Gradientenstrich nutzen nun kleinere normalisierte Stroke-Widths, damit der
  SVG-Haken weniger stark über die sichtbare Rasterkontur hinausläuft.
- Die aktive Plan-B-Rotation bleibt erhalten; `DLG0021` ist weiterhin ein
  Qualitätskandidat, aber der isolierte Einzellauf verbessert die harte
  Pixelmetrik gegenüber Run TD leicht.

## Perception-Lerneffekt

- `DLG0021` bleibt `nur Sonderfall`: Die Bilddetektion allein liefert weiterhin
  keinen ausreichend stabilen Checkbox-/Checkmark-Seed. Der robuste Pfad ist der
  beschreibungsbasierte, katalogfreie Geometry-IR-Contract mit `RectBorder` und
  `PolygonPath`-Haken.

## Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_description_contract_helpers.py::test_description_parser_attaches_dlg_style_checkbox_checkmark_geometry_ir tests/detailtests/test_description_contract_helpers.py::test_geometry_ir_renderer_emits_checkmark_stroke_gradient` läuft grün.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün und meldet weiterhin `0 occurrences`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-dlg0021-runTF --start DLG0021 --end DLG0021 --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; der isolierte Kandidatenfehler sinkt auf `52.051505` und `Mean-Delta²=24454.230469`.

## Ergebnis

`DLG0021` bleibt auf dem katalogfreien Description-Geometry-IR-Pfad. Das Stroke-
Feintuning verbessert die isolierte Pixelmetrik leicht, ohne neue Runtime-ID-
Kopplung einzuführen. Der nächste sinnvolle Schritt ist entweder weiteres
Farb-/Kontur-Feintuning für `DLG0021` oder die erneute Rotation zu `GE1410_L`.
