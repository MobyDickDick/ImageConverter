# Nächstes Arbeitspaket – Run GW (2026-05-17)

## Definition
Das **nächste Arbeitspaket** bleibt als wiederverwendbarer Begriff die feste Kombination aus:
1. nächster dokumentierter Aufgabe,
2. genau einer gekoppelten Plan-B-Aufgabe,
3. nächstem Bild aus `artifacts/converted_images/reports/summaries/not_satisfactory_converted_images.csv`.

## 1) Nächste dokumentierte Aufgabe
- Befehl:
  - `PYENV_VERSION=3.10.20 python -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_ac0812_only -q`
- Ergebnis: `1 passed`, Exit `0`.
- Log: `artifacts/converted_images/reports/T5_ac0812_timeoutpath_probe_2026-05-17_runGW.log`

## 2) Gekoppelte Plan-B-Aufgabe
- Befehl:
  - `PYTHONPATH=. python3 tools/plan_b_synthetic_probe.py "Bildbeschreibung: Kreis mit horizontalem Griff links und Beschriftung rF." --variant AC0030_L --output-dir artifacts/converted_images/reports`
- Ergebnis: `status=ok`, Exit `0`.
- Hinweis: Die bekannte OpenCV/Numpy-Umgebungswarnung wurde ausgegeben, ohne den Exit-Code zu beeinflussen.
- Log: `artifacts/converted_images/reports/AC0030_L_planb_synthetic_2026-05-17_runGW.log`

## 3) Nächstes CSV-Bild
- Quelle: `artifacts/converted_images/reports/summaries/not_satisfactory_converted_images.csv`
- Nächster Eintrag nach zuletzt dokumentiertem `AC0030`: `AC0030_L`
- Bearbeitung:
  - `PYTHONPATH=. timeout 240 python3 -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir artifacts/converted_images --start AC0030_L --end AC0030_L`
- Ergebnis: Exit `0`.
- Log: `artifacts/converted_images/reports/AC0030_L_single_2026-05-17_runGW.log`
- Tracking: `AC0030_L` wurde in der CSV als bearbeitet (`in samples=yes`) markiert.

## Kurzfazit
Das Arbeitspaket wurde wieder vollständig in der gewünschten 3er-Kombination durchgeführt; der Begriff **„nächstes Arbeitspaket“** bleibt damit in der Doku direkt referenzierbar.
