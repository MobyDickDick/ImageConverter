# Nächstes Arbeitspaket – SE0041_1 Picofine-Rule-Stroke-Width-Probes Run VB (2026-07-04)

Run VB rotiert nach `docs/next_arbeitspaket_2026-07-04_runVA.md` auf den
aktiven Plan-B-Kandidaten `SE0041_1`. Der Fokus bleibt katalogfrei: Die
bestehenden `HorizontalRule`-/`VerticalRule`-Stroke-Width-Probes für Square-
Badge-Arme und -Stems erhalten eine picofeine absolute Stufe, damit dünne
Regelkonturen noch präziser gegen Antialiasing-Rasterlagen bewertet werden
können.

## 1) Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt für `RectBorder`,
  `HorizontalRule` und `VerticalRule` mit `stroke_width` zusätzlich zu den
  vorhandenen Schrittweiten nun picofeine `0.00015625`-Offsets in beide
  Richtungen.
- Die Änderung ist deterministisch und katalogfrei; sie koppelt weder an
  `SE0041_1` noch an eine andere Runtime-Bild-ID.
- Ein Detailtest sichert die neue Kandidatenstufe explizit gegen Regression ab.

## 2) Perception-Lerneffekt

`SE0041_1` bleibt `nur Sonderfall`: Der Square-Badge-Seed stammt weiterhin aus
der beschreibungsbasierten AC0811-Aliasableitung, nicht aus einer vollständig
stabilen Bilddetektion. Run VB verfeinert nur den allgemeinen Rule-/RectBorder-
Stroke-Suchraum, der auch für andere katalogfreie Square-Badge- und Regel-
Primitive nutzbar ist.

## 3) Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rule_stroke_width_with_picofine_absolute_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rule_stroke_width_with_nanofine_absolute_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rule_stroke_width_with_microfine_absolute_probe` läuft grün mit `3 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün und bestätigt weiterhin `0` Runtime-ID-Vorkommen.
- `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-se0041-runVB --start SE0041_1 --end SE0041_1 --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; die isolierte SE0041_1-Metrik bleibt stabil bei `Mean-Delta²=2436.707764` und `Fehler/Pixel=0.015932`.

## 4) Ergebnis / nächster Schritt

Run VB schließt den dokumentierten SE0041_1-Feinschritt ab. Rule- und
RectBorder-Stroke-Widths können nun katalogfrei picofeine Zwischenbreiten
bewerten; der isolierte SE0041_1-Einzellauf bleibt metrisch stabil. Das nächste
Arbeitspaket kann in der aktiven Plan-B-Rotation zu `GE9012_6M` wechseln oder
weitere allgemeine Antialiasing-/Stroke-Feintuning-Probes untersuchen.
