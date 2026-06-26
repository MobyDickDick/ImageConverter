# Nächstes Arbeitspaket – SE0041_1 Square-Badge-Feintuning Run TE (2026-06-26)

Run TE rotiert nach Run SZ auf den in `PLAN_B_KANDIDATEN.md` dokumentierten
Folgekandidaten `SE0041_1`. Fokus ist das Pixel-Feintuning des bereits in Run SU
eingeführten katalogfreien Square-Badge-Seeds aus der AC0811-Aliasbeschreibung.

## Änderungen

- Square-Badge-Heads können nun explizite, gemessene Kopf-Füll- und
  Konturfarben rendern, statt auf Graustufen-`fill_gray`/`stroke_gray`
  beschränkt zu bleiben.
- Der Square-Badge-Variantpfad registriert den Kopf als nahezu volle rote
  28×28-Kachel und unterdrückt den aus der AC0811-Referenz geerbten rechten
  Kreis-Connector, während der untere graue Stem erhalten bleibt.
- Detailtests sichern die farbige Square-Badge-Ausgabe zusätzlich zur
  bestehenden Rechteck-statt-Kreis-Invariante ab.

## Artefakte

- Isolierter Repro-Ausgabeordner: `/tmp/ic-se0041-after2`

## Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/test_image_composite_converter.py::test_generate_badge_svg_renders_square_badge_head tests/test_image_composite_converter.py::test_generate_badge_svg_renders_square_badge_head_with_explicit_colors` läuft grün mit `2 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-se0041-after2 --start SE0041_1 --end SE0041_1 --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün.

## Ergebnis

`SE0041_1` bleibt auf dem katalogfreien semantischen Square-Badge-Pfad. Die
isolierte CLI-Metrik verbessert sich gegenüber dem Vorlauf von
`Mean-Delta²=30095.613281` auf `7242.835938` (`Fehler/Pixel=0.02167665`). Das
nächste Plan-B-Paket kann auf `GE9012_6M` rotieren oder bei Bedarf weitere
SE0041-Antialiasing-/Stem-Feinheiten nachziehen.
