# Nächstes Arbeitspaket – GE9021_7M U-Loop-Primitive Run SR (2026-06-25)

Run SR rotiert nach dem GE1001-Checkmark-Paket auf den nächsten dokumentierten
Plan-B-Kandidaten aus `PLAN_B_KANDIDATEN.md`: `GE9021_7M`. Der PF8-Linkage-
Report führte diesen Kandidaten bisher als Linienhinweis `nur Sonderfall`.

## Änderungen

- Die GE9021-Beschreibung in beiden Beschreibungskopien wurde von der
  referenziellen BackBottom-Kurzform auf eine katalogfreie konkrete
  Bildbeschreibung umgestellt: schmaler weißer Hintergrund, zwei senkrechte
  gelbe Linien und ein unterer runder gelber U-Bogen.
- `buildGeometryIrFromDescriptionImpl(...)` erkennt nun allgemeine gelbe
  U-Form-/U-Bogen-Beschreibungen ohne Katalog-ID und erzeugt dafür einen
  neutralen Geometry-IR-Seed aus weißem `ColorPatch` und gelbem `PolygonPath`.
- Der neue Primitive-Contract `u_loop_primitive_decomposition_v1` zerlegt die
  Form in linken vertikalen Schenkel, unteren Bogenverbinder und rechten
  vertikalen Schenkel.
- Ein neutraler Detailtest sichert die Beschreibung-zu-Geometry-IR-Übersetzung
  ohne GE9021-Namen ab.

## Artefakte

- `artifacts/converted_images/reports/GE9021_7M_plan_b_runSR_2026-06-25.log`
- `artifacts/converted_images/reports/GE9021_7M_plan_b_runSR_after_2026-06-25.log`

## Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_description_contract_helpers.py::test_description_parser_attaches_generic_yellow_u_loop_geometry_ir tests/detailtests/test_description_contract_helpers.py::test_description_parser_attaches_generic_checkmark_geometry_ir tests/detailtests/test_description_contract_helpers.py::test_description_parser_checkmark_geometry_ir_is_filename_invariant` läuft grün mit `3 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün und meldet weiterhin `0 occurrences`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ge9021-runsr-after --start GE9021_7M --end GE9021_7M --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün und protokolliert die neue konkrete Beschreibung.

## Ergebnis

Der nächste Plan-B-Kandidat besitzt nun wie GE1001 einen katalogfreien,
beschreibungsgetriebenen Primitive-Seed. Der reale CLI-Pfad bleibt aktuell noch
im elementweisen Fallback und die Qualitätsmetrik bleibt bei
`Mean-Delta²=8922.235352`; der fachliche Beschreibungsmangel ist jedoch
beseitigt und die U-Loop-Geometrie ist als neutraler Contract für die weitere
Pipeline-Anbindung verfügbar.
