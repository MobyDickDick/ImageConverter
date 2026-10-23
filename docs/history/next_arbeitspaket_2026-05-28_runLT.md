# Nächstes Arbeitspaket – Run LT (2026-05-28)

Dieses Arbeitspaket bearbeitet den nach Run LS dokumentierten Anschluss: Aus den neuen Scorecard-Telemetrie-Kennzahlen wird eine explizite Drift-Grenze für künftige Batchläufe abgeleitet und im bestehenden Summary-Artefakt festgehalten.

## 1) Nächste dokumentierte Aufgabe: Drift-Grenze für Scorecard-Telemetrie

- Erweitert:
  - `chain_phase_telemetry_summary.txt` enthält zusätzlich zu R5- und Scorecard-Aggregaten nun einen Drift-Gate-Block.
  - Neue Felder: `drift_status`, `drift_reasons`, `drift_max_mean_error_per_pixel`, `drift_max_mean_delta2`, `drift_max_non_green`.
- Standardgrenzen:
  - `drift_max_mean_error_per_pixel=0.05`
  - `drift_max_mean_delta2=18.0`
  - `drift_max_non_green=0`
- Konfiguration:
  - `ICC_CHAIN_DRIFT_MAX_MEAN_ERROR_PER_PIXEL`
  - `ICC_CHAIN_DRIFT_MAX_MEAN_DELTA2`
  - `ICC_CHAIN_DRIFT_MAX_NON_GREEN`
- Nutzen:
  - Batchläufe erhalten direkt einen maschinenlesbaren Pass/Warn-Status für Drift-Vergleiche.
  - Grenzwertverletzungen werden über `drift_reasons` stabil benannt und können in Folgechecks ausgewertet werden.

## 2) Sichernde Detailtests

- Befehl:
  - `python -m pytest -q tests/detailtests/test_batch_reporting_helpers.py`
- Ergebnis:
  - Exit `0`
  - `5 passed in 0.10s`
- Abdeckung:
  - Drift-Gate `pass` bei grünen Scorecard-Kennzahlen.
  - Drift-Gate `warn` bei überschrittenen Grenzwerten und nicht-grünem Status.

## 3) Erweiterter Detailtest-Block

- Befehl:
  - `PYENV_VERSION=3.10.20 python -m pytest -q tests/detailtests/test_batch_reporting_helpers.py tests/detailtests/test_chain_telemetry_helpers.py tests/detailtests/test_conversion_finalization_helpers.py`
- Ergebnis:
  - Exit `0`
  - `25 passed in 0.33s`

## 4) Volltest

- Befehl:
  - `PYENV_VERSION=3.10.20 timeout 300 python -m pytest -q -rs`
- Ergebnis:
  - Exit `0`
  - `563 passed, 5 warnings in 10.10s`

## Fazit

Der nach Run LS dokumentierte Anschluss ist umgesetzt: Die Scorecard-Telemetrie besitzt jetzt eine explizite, konfigurierbare Drift-Grenze, die direkt im Batch-Summary-Artefakt sichtbar wird.
