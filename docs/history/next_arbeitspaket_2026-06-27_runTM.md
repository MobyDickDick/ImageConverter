# Nächstes Arbeitspaket – GE9013_1M BackBottom-Farbregistrierung Run TM (2026-06-27)

Run TM arbeitet nach Run TL den nächsten dokumentierten Plan-B-Kandidaten aus
`PLAN_B_KANDIDATEN.md` ab: `GE9013_1M` nutzt bereits den katalogfreien
BackBottom-/hellgraues-Quadrat-Contract, hatte aber noch eine deutlich sichtbare
Farbabweichung im vertikalen 20×60-Canvas.

## Änderungen

- Die generische Geometry-IR-Elementoptimierung kennt nun zusätzlich warme helle
  Füllfarb-Probes für `RectBorder`-/`ColorPatch`-Elemente. Diese Palette ist
  katalogfrei und wird nur akzeptiert, wenn der reale Renderfehler sinkt.
- Ein Regressionstest sichert, dass neutrale Rechteck-IRs nicht nur zu kühlen,
  sondern auch zu warmen hellen Füllungen verfeinert werden können.
- Der echte `GE9013_1M`-Einzellauf bleibt auf `status=non_composite_description_geometry_ir`,
  wählt aber nach der Elementverfeinerung `fill="#f2b8b4"` für das
  BackBottom-Rechteck.

## Perception-Lerneffekt

- `GE9013_1M` bleibt `nur Sonderfall`: Die reine Bilddetektion ist nicht der
  primäre stabile Pfad. Der robuste Pfad ist weiterhin der
  beschreibungsbasierte, katalogfreie BackBottom-/hellgraues-Quadrat-Contract,
  jetzt mit neutraler warmer Füllfarb-Feinregistrierung.

## Artefakte

- Isolierter Repro-Ausgabeordner: `/tmp/ic-ge9013-runTM`

## Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py tests/test_image_composite_converter.py::test_backbottom_square_description_scales_to_vertical_variant_canvas tests/test_image_composite_converter.py::test_backbottom_square_description_is_preferred_semantic_geometry_candidate` läuft grün mit `11 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün und meldet weiterhin `0 occurrences`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ge9013-runTM --start GE9013_1M --end GE9013_1M --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; der isolierte Kandidatenfehler sinkt von `46.570278` auf `42.919167`, und `Mean-Delta²` sinkt im lokalen Einzellauf von `19333.585938` auf `12989.524414`.

## Ergebnis

`GE9013_1M` nutzt weiterhin denselben katalogfreien Description-Geometry-IR-Pfad,
rendert den vertikalen BackBottom-Füllton aber nach der neutralen warmen
Elementregistrierung pixelnäher. Das nächste Paket kann wieder in der aktiven
Plan-B-Liste rotieren oder das verbleibende BackBottom-/Diff-Feintuning
fortsetzen.
