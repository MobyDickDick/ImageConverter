# Nächstes Arbeitspaket – Run JD (2026-05-24)

Dieses Arbeitspaket wurde als feste Kombination ausgeführt mit Fokus auf `AC0030`.

## 1) Nächste dokumentierte Aufgabe (TB-A3)
- Befehl:
  - `PYENV_VERSION=3.10.20 timeout 240 python -m pytest tests/test_satisfactory_regression_battery.py::test_satisfactory_successful_variants_reconversion_keeps_or_improves_quality -q`
- Ergebnis:
  - `1 skipped, 5 warnings`, Exit `0`.
- Log:
  - `artifacts/converted_images/reports/TB_A3_timeout_probe_2026-05-24_runJD.log`

## 2) Gekoppelte Plan-B-Aufgaben (AC0030-Familie)
- Befehle:
  - `PYTHONPATH=. python3 tools/plan_b_synthetic_probe.py "Bildbeschreibung: Luftkühler." --variant AC0030 --output-dir artifacts/converted_images/reports`
  - `PYTHONPATH=. python3 tools/plan_b_synthetic_probe.py "Bildbeschreibung: Stilisierte Röhren." --variant AC0030_L --output-dir artifacts/converted_images/reports`
  - `PYTHONPATH=. python3 tools/plan_b_synthetic_probe.py "Bildbeschreibung: Stilisierte Röhren." --variant AC0030_M --output-dir artifacts/converted_images/reports`
  - `PYTHONPATH=. python3 tools/plan_b_synthetic_probe.py "Bildbeschreibung: Stilisierte Röhren." --variant AC0030_S --output-dir artifacts/converted_images/reports`
- Ergebnis:
  - Alle Läufe `status=ok`, Exit `0`.
- Logs:
  - `artifacts/converted_images/reports/AC0030_planb_synthetic_2026-05-24_runJD.log`
  - `artifacts/converted_images/reports/AC0030_L_planb_synthetic_2026-05-24_runJD.log`
  - `artifacts/converted_images/reports/AC0030_M_planb_synthetic_2026-05-24_runJD.log`
  - `artifacts/converted_images/reports/AC0030_S_planb_synthetic_2026-05-24_runJD.log`

## 3) Einzelkonvertierungen AC0030 / AC0030_L / AC0030_M / AC0030_S
- Befehle:
  - `PYTHONPATH=. timeout 240 python3 -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir artifacts/converted_images --start AC0030 --end AC0030`
  - `PYTHONPATH=. timeout 240 python3 -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir artifacts/converted_images --start AC0030_L --end AC0030_L`
  - `PYTHONPATH=. timeout 240 python3 -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir artifacts/converted_images --start AC0030_M --end AC0030_M`
  - `PYTHONPATH=. timeout 240 python3 -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir artifacts/converted_images --start AC0030_S --end AC0030_S`
- Ergebnis:
  - Alle Läufe Exit `0`; Plan-B-Sample-Vergleich für AC0030-Familie aktiv.
- Logs:
  - `artifacts/converted_images/reports/AC0030_single_2026-05-24_runJD.log`
  - `artifacts/converted_images/reports/AC0030_L_single_2026-05-24_runJD.log`
  - `artifacts/converted_images/reports/AC0030_M_single_2026-05-24_runJD.log`
  - `artifacts/converted_images/reports/AC0030_S_single_2026-05-24_runJD.log`

## Volltest (final)
- Befehl:
  - `PYENV_VERSION=3.10.20 timeout 300 python -m pytest -q -rs`
- Ergebnis:
  - `530 passed, 5 warnings`, Exit `0`.
- Log:
  - `artifacts/converted_images/reports/pytest_full_2026-05-24_runJD.log`

## Hinweis zu Dateinameingabe
- Der gewünschte Name `AC0030_L.jgp` wurde als offensichtlicher Tippfehler zu `AC0030_L.jpg` interpretiert (Datei vorhanden unter `artifacts/images_to_convert/AC0030_L.jpg`).
