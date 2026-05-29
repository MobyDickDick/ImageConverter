# Nächstes Arbeitspaket – Run LS (2026-05-28)

Dieses Arbeitspaket bearbeitet den nach Run LR dokumentierten Anschluss: Die R5-Ketten-Telemetrie wird in die bestehende Scorecard-/Baseline-Auswertung eingebunden und mit sichernden Tests abgeschlossen.

## 1) Nächste dokumentierte Aufgabe: Telemetrie in Scorecard/Baseline integrieren

- Erweitert:
  - `chain_phase_telemetry.csv` enthält zusätzlich zu den R5-Phasenfeldern nun die Scorecard-Felder `status`, `error_per_pixel` und `mean_delta2` je Variante.
  - `chain_phase_telemetry_summary.txt` enthält neben den R5-Aggregaten nun auch Scorecard-/Baseline-Kennzahlen: `scorecard_row_count`, `semantic_ok_count`, `non_green_count`, `mean_error_per_pixel`, `mean_delta2`.
- Nutzen:
  - R5-Telemetrie kann direkt mit der bestehenden Qualitäts-/Bestlist-Bewertung abgeglichen werden.
  - Batchläufe liefern eine kompakte Basis für Drift- und Abnahmevergleiche, ohne die Telemetrie separat gegen die Scorecard nachjoinen zu müssen.

## 2) Sichernde Detailtests

- Befehl:
  - `PYENV_VERSION=3.10.20 python -m pytest -q tests/detailtests/test_batch_reporting_helpers.py tests/detailtests/test_chain_telemetry_helpers.py tests/detailtests/test_conversion_finalization_helpers.py`
- Ergebnis:
  - Exit `0`
  - `23 passed in 0.17s`
- Log:
  - `artifacts/converted_images/reports/r5_scorecard_telemetry_detailtests_2026-05-28_runLS.log`

## 3) Volltest

- Befehl:
  - `PYENV_VERSION=3.10.20 timeout 300 python -m pytest -q -rs`
- Ergebnis:
  - Exit `0`
  - `561 passed, 5 warnings in 8.44s`
- Log:
  - `artifacts/converted_images/reports/pytest_full_2026-05-28_runLS.log`

## Fazit

Der dokumentierte Anschluss nach Run LR ist umgesetzt: Die Ketten-Telemetrie ist jetzt direkt scorecardfähig und trägt die wichtigsten Qualitätskennzahlen in CSV und Summary. Die gezielten Detailtests und die Vollsuite sind grün.
