# Nächstes Arbeitspaket – Run HA (2026-05-19)

## Definition
Das **nächste Arbeitspaket** bleibt als wiederverwendbarer Begriff die feste Kombination aus:
1. nächster dokumentierter Aufgabe,
2. genau einer gekoppelten Plan-B-Aufgabe,
3. nächstem Bild aus `artifacts/converted_images/reports/reports/summaries/not_satisfactory_converted_images.csv`.

## 1) Nächste dokumentierte Aufgabe
- Befehl:
  - `PYENV_VERSION=3.10.20 PYTHONPATH=. timeout 240 pyenv exec python -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_ac0812_only -q`
- Ergebnis: `1 passed`, Exit `0`.
- Log: `artifacts/converted_images/reports/T5_ac0812_timeoutpath_probe_2026-05-19_runHA.log`

## 2) Gekoppelte Plan-B-Aufgabe
- Befehl:
  - `PYTHONPATH=. python3 tools/plan_b_synthetic_probe.py "Bildbeschreibung: Kreis mit horizontalem Griff links und Beschriftung rF." --variant AC0023 --output-dir artifacts/converted_images/reports`
- Ergebnis: `status=ok`, Exit `0`.
- Hinweis: Die bekannte OpenCV/Numpy-Umgebungswarnung wurde ausgegeben, ohne den Exit-Code zu beeinflussen.
- Log: `artifacts/converted_images/reports/AC0023_planb_synthetic_2026-05-19_runHA.log`

## 3) Nächstes CSV-Bild
- Quelle: `artifacts/converted_images/reports/reports/summaries/not_satisfactory_converted_images.csv`
- Nächster Eintrag nach zuletzt dokumentiertem `AC0022`: `AC0023`
- Bearbeitung:
  - `PYTHONPATH=. timeout 240 python3 -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir artifacts/converted_images --start AC0023 --end AC0023`
- Ergebnis: Exit `0`.
- Log: `artifacts/converted_images/reports/AC0023_single_2026-05-19_runHA.log`
- Tracking: `AC0023` wurde in der CSV als bearbeitet (`in samples=yes`) markiert.

## Testbatterie (nachgeführt)
- Befehl:
  - `PYENV_VERSION=3.10.20 pytest -q tests/detailtests/test_conversion_execution_helpers.py tests/detailtests/test_iteration_setup_helpers.py tests/detailtests/test_quality_config_helpers.py`
- Ergebnis: `17 passed, 3 xfailed`, Exit `0`.

## Kurzfazit
Das Arbeitspaket wurde vollständig in der gewünschten 3er-Kombination ausgeführt und die stabile Testbatterie läuft weiterhin grün (mit den bekannten drei xfails).
