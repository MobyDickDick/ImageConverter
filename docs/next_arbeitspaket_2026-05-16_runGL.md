# Nächstes Arbeitspaket – Run GL (2026-05-16)

## Definition
Das **nächste Arbeitspaket** bleibt die feste Kombination aus:
1. nächster dokumentierter Aufgabe,
2. genau einer gekoppelten Plan-B-Aufgabe,
3. nächstem Bild aus `artifacts/converted_images/reports/summaries/not_satisfactory_converted_images.csv`.

## 1) Nächste dokumentierte Aufgabe
- Befehl:
  - `PYENV_VERSION=3.10.20 PYTHONPATH=. timeout 240 pyenv exec python -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_ac0812_only -q`
- Ergebnis: `1 passed`, Exit `0`.
- Log: `artifacts/converted_images/reports/T5_ac0812_timeoutpath_probe_2026-05-16_runGL.log`

## 2) Gekoppelte Plan-B-Aufgabe
- Befehl:
  - `PYTHONPATH=. python3 tools/plan_b_synthetic_probe.py "Bildbeschreibung: Kreis mit horizontalem Griff links und Beschriftung rF." --variant AC0024 --output-dir artifacts/converted_images/reports`
- Ergebnis: `status=ok`, Exit `0`.
- Log: `artifacts/converted_images/reports/AC0024_planb_synthetic_2026-05-16_runGL.log`

## 3) Nächstes CSV-Bild
- Quelle: `artifacts/converted_images/reports/summaries/not_satisfactory_converted_images.csv`
- Nächster Eintrag nach zuletzt dokumentiertem `AC0023`: `AC0024`
- Bearbeitung:
  - `PYTHONPATH=. timeout 240 python3 -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir artifacts/converted_images --start AC0024 --end AC0024`
- Ergebnis: Exit `0`.
- Log: `artifacts/converted_images/reports/AC0024_single_2026-05-16_runGL.log`

## Kurzfazit
Das Arbeitspaket wurde vollständig in der 3er-Kombination durchgeführt und erfolgreich abgeschlossen.
