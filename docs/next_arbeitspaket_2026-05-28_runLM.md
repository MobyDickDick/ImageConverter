# Nächstes Arbeitspaket – Run LM (2026-05-28)

Dieses Arbeitspaket wurde im etablierten 3er-Schema ausgeführt und mit vollständigem Testlauf abgeschlossen.

## 1) Nächste dokumentierte Aufgabe (T6.3)

- Befehl:
  - `PYENV_VERSION=3.10.20 PYTHONPATH=. timeout 180 pyenv exec python -u -m pytest tests/test_image_composite_converter.py::test_make_badge_params_keeps_ac0838_m_circle_near_full_width_for_voc_layout -q`
- Ergebnis:
  - Exit `0`
  - `1 skipped, 5 warnings in 3.66s`
- Log:
  - `artifacts/converted_images/reports/T6_3_ac0838M_isolation_2026-05-28_runLM.log`

## 2) Gekoppelte Plan-B-Aufgabe (T6-PB)

- Befehl:
  - `PYENV_VERSION=3.10.20 python -m pytest -q tests/detailtests/test_global_search_optimization_helpers.py::test_global_search_skips_deterministic_track_after_strong_stochastic_gain`
- Ergebnis:
  - Exit `0`
  - `1 passed in 0.13s`
- Log:
  - `artifacts/converted_images/reports/t6_planb_singletest_2026-05-28_runLM.log`

## 3) Nächstes Bild (Plan-B-Kandidat)

- Ausgeführt als Syntheseprobe für `AC0130_M`.
- Befehl:
  - `PYENV_VERSION=3.10.20 python -m tools.plan_b_synthetic_probe "Bildbeschreibung: Kreis mit horizontalem Griff links und Beschriftung rF." --variant AC0130_M --output-dir artifacts/converted_images/reports`
- Ergebnis:
  - Exit `0`
  - `status=ok`, `variant=AC0130_M`
- Log:
  - `artifacts/converted_images/reports/AC0130_M_planb_synthetic_2026-05-28_runLM.log`

## 4) Volltest (Abschluss des Arbeitspakets)

- Befehl:
  - `PYENV_VERSION=3.10.20 timeout 300 python -m pytest -q -rs`
- Ergebnis:
  - Exit `0`
  - `547 passed, 5 warnings in 5.98s`
- Log:
  - `artifacts/converted_images/reports/pytest_full_2026-05-28_runLM.log`

## Fazit

Das nächste dokumentierte Arbeitspaket wurde vollständig abgearbeitet; alle vier Schritte endeten mit Exit `0`.
