# Nächstes Arbeitspaket – Run IP (2026-05-23)

Dieses Arbeitspaket wurde als feste 3er-Kombination ausgeführt:
1. nächste dokumentierte Aufgabe,
2. genau eine gekoppelte Plan-B-Aufgabe,
3. gezielter Konvertierungsversuch für `AC0VR2_M.jpg`.

## 1) Nächste dokumentierte Aufgabe (TB-A3)
- Befehle:
  - `PYENV_VERSION=3.10.20 pyenv exec python -m tools.manage_satisfactory_baseline --variants-file successed_conversions.txt --images-dir artifacts/images_to_convert --svgs-dir artifacts/converted_images/converted_svgs --baseline-dir artifacts/regression_baseline/satisfactory`
  - `PYENV_VERSION=3.10.20 PYTHONPATH=. timeout 300 pyenv exec python -m pytest tests/test_satisfactory_regression_battery.py::test_satisfactory_successful_variants_reconversion_keeps_or_improves_quality -q`
- Ergebnis:
  - Baseline-Pfad wurde vorbereitet.
  - Testlauf endet reproduzierbar als `xfailed` (`1 xfailed, 5 warnings`, Exit `0`).
- Logs:
  - `artifacts/converted_images/reports/TB_A3_baseline_prepare_2026-05-23_runIP.log`
  - `artifacts/converted_images/reports/TB_A3_timeout_probe_2026-05-23_runIP.log`

## 2) Gekoppelte Plan-B-Aufgabe (`AC0VR2_M.svg`)
- Befehl:
  - `PYTHONPATH=. python3 -m tools.plan_b_roundtrip artifacts/images_to_convert/samples/AC0VR2_M.svg --output-dir artifacts/converted_images/reports`
- Ergebnis:
  - Plan-B-Roundtrip wurde vollständig ausgeführt.
  - Resultat: `status=failed_svg`, Artefakt `Failed_AC0VR2_M.svg` erzeugt.
- Log:
  - `artifacts/converted_images/reports/AC0VR2_M_planb_roundtrip_2026-05-23_runIP.log`

## 3) Abschließender Versuch: `AC0VR2_M.jpg` konvertieren
- Befehl:
  - `PYTHONPATH=. timeout 240 python3 -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir artifacts/converted_images --start AC0VR2_M --end AC0VR2_M`
- Ergebnis:
  - Lauf mit Exit `0` abgeschlossen.
  - Bewertung des erzeugten SVG-Artefakts: `Embedded-Raster-SVG erkannt`, daher als fehlgeschlagen markiert.
- Log:
  - `artifacts/converted_images/reports/AC0VR2_M_single_2026-05-23_runIP.log`

## Fazit
Das Arbeitspaket wurde vollständig durchgeführt: dokumentierter TB-A3-Pfad, gekoppelte Plan-B-Aufgabe für `AC0VR2_M.svg` sowie ein abschließender direkter Konvertierungsversuch für `AC0VR2_M.jpg`.
