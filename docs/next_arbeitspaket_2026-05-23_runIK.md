# Nächstes Arbeitspaket – Run IK (2026-05-23)

Dieses Arbeitspaket wurde wieder als feste 3er-Kombination ausgeführt:
1. nächste dokumentierte Aufgabe,
2. genau eine gekoppelte Plan-B-Aufgabe,
3. nächstes Bild bzw. angeforderter Re-Run.

## 1) Nächste dokumentierte Aufgabe (TB-A3)
- Befehl:
  - `PYENV_VERSION=3.10.20 pyenv exec python -m tools.manage_satisfactory_baseline --variants-file successed_conversions.txt --images-dir artifacts/images_to_convert --svgs-dir artifacts/converted_images/converted_svgs --baseline-dir artifacts/regression_baseline/satisfactory`
  - `PYENV_VERSION=3.10.20 PYTHONPATH=. timeout 300 pyenv exec python -m pytest tests/test_satisfactory_regression_battery.py::test_satisfactory_successful_variants_reconversion_keeps_or_improves_quality -q`
- Ergebnis:
  - Baseline vorbereitet (`Prepared baseline pairs: 25`).
  - Priorisierter TB-A3-Lauf grün: `1 passed, 5 warnings`, Exit `0`.
- Logs:
  - `artifacts/converted_images/reports/TB_A3_baseline_prepare_2026-05-23_runIK.log`
  - `artifacts/converted_images/reports/TB_A3_timeout_probe_2026-05-23_runIK.log`

## 2) Gekoppelte Plan-B-Aufgabe (`AC0882_L.svg` aus Samples)
- Befehl:
  - `PYTHONPATH=. timeout 240 python3 -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert/samples --output-dir artifacts/converted_images --start AC0882_L --end AC0882_L`
- Ergebnis:
  - Sample-basierter Plan-B-Einzellauf erfolgreich, Exit `0`.
- Log:
  - `artifacts/converted_images/reports/AC0882_L_planb_samples_single_2026-05-23_runIK.log`

## 3) Erneute Konvertierung `AC0882_L.jpg`
- Befehl:
  - `PYTHONPATH=. timeout 240 python3 -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir artifacts/converted_images --start AC0882_L --end AC0882_L`
- Ergebnis:
  - Re-Run für `AC0882_L.jpg` erfolgreich, Exit `0`.
- Log:
  - `artifacts/converted_images/reports/AC0882_L_jpg_reconvert_2026-05-23_runIK.log`

## Fazit
Das nächste Arbeitspaket wurde vollständig in der gewünschten Kombination durchgeführt. Die dokumentierte Aufgabe TB-A3 bleibt grün, die angeforderte Plan-B-Aufgabe auf Sample-Basis wurde erledigt und die erneute JPG-Konvertierung für `AC0882_L` ist erfolgreich durchgelaufen.
