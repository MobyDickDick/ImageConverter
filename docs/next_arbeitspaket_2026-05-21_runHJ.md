# Nächstes Arbeitspaket – Run HJ (2026-05-21)

## Definition
Das **nächste Arbeitspaket** bleibt als wiederverwendbarer Begriff die feste Kombination aus:
1. nächster dokumentierter Aufgabe,
2. genau einer gekoppelten Plan-B-Aufgabe,
3. nächstem Bild aus `artifacts/converted_images/reports/reports/summaries/not_satisfactory_converted_images.csv`.

## 1) Nächste dokumentierte Aufgabe
- Befehl:
  - `PYENV_VERSION=3.10.20 PYTHONPATH=. timeout 240 pyenv exec python -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_ac0812_only -q`
- Ergebnis: `1 passed` (mit `5 warnings`), Exit `0`.
- Log: `artifacts/converted_images/reports/T5_ac0812_timeoutpath_probe_2026-05-21_runHJ.log`

## 2) Gekoppelte Plan-B-Aufgabe
- Befehl:
  - `PYTHONPATH=. python3 tools/plan_b_synthetic_probe.py "Bildbeschreibung: Kreis mit horizontalem Griff links und Beschriftung rF." --variant AC0030_L --output-dir artifacts/converted_images/reports`
- Ergebnis: `status=ok`, Exit `0`.
- Log: `artifacts/converted_images/reports/AC0030_L_planb_synthetic_2026-05-21_runHJ.log`

## 3) Nächstes CSV-Bild
- Quelle: `artifacts/converted_images/reports/reports/summaries/not_satisfactory_converted_images.csv`
- Nächster Eintrag nach zuletzt dokumentiertem `AC0030`: `AC0030_L`
- Bearbeitung:
  - `PYTHONPATH=. timeout 240 python3 -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir artifacts/converted_images --start AC0030_L --end AC0030_L`
- Ergebnis: Exit `0`.
- Log: `artifacts/converted_images/reports/AC0030_L_single_2026-05-21_runHJ.log`

## Testbatterie (nachgeführt)
- Befehl:
  - `PYENV_VERSION=3.10.20 pytest -q tests/detailtests/test_conversion_execution_helpers.py tests/detailtests/test_iteration_setup_helpers.py tests/detailtests/test_quality_config_helpers.py`
- Ergebnis: `20 passed`, Exit `0`.
- Log: `artifacts/converted_images/reports/test_battery_2026-05-21_runHJ.log`

## Kurzfazit
Das Arbeitspaket wurde vollständig in der definierten 3er-Kombination ausgeführt. Der Kurztestpfad und die begleitende Testbatterie bleiben grün; der AC0030_L-Einzellauf endete mit Exit `0`.
- **Blocker:** Der bekannte N1/N2-Vollbereichsblocker (Timeout/Laufzeit) bleibt davon unabhängig bestehen.
- **Nächster sinnvoller Schritt:** Dasselbe Arbeitspaket-Schema mit dem nächsten CSV-Eintrag (`AC0030_M`) fortsetzen.
