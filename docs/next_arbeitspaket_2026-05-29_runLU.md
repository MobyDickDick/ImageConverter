# Nächstes Arbeitspaket – Run LU (2026-05-29)

Dieses Arbeitspaket bearbeitet den nach Run LT dokumentierten Anschluss: Die Drift-Grenze der Scorecard-Telemetrie wird in einen automatisierten Abnahmecheck für konkrete Batch-Artefakte überführt.

## 1) Nächste dokumentierte Aufgabe: Drift-Gate als Artefakt-Check

- Eingeführt:
  - `tools/check_chain_telemetry_drift_gate.py` prüft ein vorhandenes `chain_phase_telemetry_summary.txt` und liefert einen prozessfähigen Exit-Code.
  - `checkChainTelemetryDriftSummaryImpl(...)` wertet das Summary-Artefakt maschinenlesbar aus.
  - `readKeyValueReportImpl(...)` liest einfache `key=value`-Reports stabil für Folgechecks ein.
- Verhalten:
  - `drift_status=pass` → Exit `0`, Ergebnis `accepted=True`.
  - `drift_status=warn` → Exit `1`, stabile Reason-Liste aus `drift_reasons`.
  - fehlendes Summary oder fehlender `drift_status` → Exit `1` mit expliziten Reasons (`summary_missing` bzw. `drift_status_missing`).
- Nutzen:
  - Batch-Artefakte können in Shell-/CI-/Pre-Commit-Gates direkt gegen die dokumentierte Drift-Grenze geprüft werden.
  - Der Check ist unabhängig vom Batchlauf selbst und kann nachträglich auf archivierte Reports angewendet werden.

## 2) Sichernde Detailtests

- Befehl:
  - `python -m pytest -q tests/detailtests/test_batch_reporting_helpers.py`
- Ergebnis:
  - Exit `0`
  - `8 passed in 0.10s`
- Abdeckung:
  - Drift-Artefakt `pass` wird akzeptiert.
  - Drift-Artefakt `warn` wird mit stabiler Reason-Liste abgelehnt.
  - Fehlendes Summary wird deterministisch als `summary_missing` abgelehnt.

## 3) Artefakt-Check-Probe

- Befehl:
  - `tmpdir=$(mktemp -d); printf 'drift_status=pass\ndrift_reasons=\n' > "$tmpdir/chain_phase_telemetry_summary.txt"; python tools/check_chain_telemetry_drift_gate.py "$tmpdir/chain_phase_telemetry_summary.txt"; status=$?; rm -rf "$tmpdir"; exit $status`
- Ergebnis:
  - Exit `0`
  - `PASS chain telemetry drift gate: .../chain_phase_telemetry_summary.txt`

## 4) Erweiterter Detailtest-Block

- Befehl:
  - `PYENV_VERSION=3.10.20 python -m pytest -q tests/detailtests/test_batch_reporting_helpers.py tests/detailtests/test_chain_telemetry_helpers.py tests/detailtests/test_conversion_finalization_helpers.py`
- Ergebnis:
  - Exit `0`
  - `28 passed in 0.27s`

## 5) Volltest

- Befehl:
  - `PYENV_VERSION=3.10.20 timeout 300 python -m pytest -q -rs`
- Ergebnis:
  - Exit `0`
  - `566 passed, 5 warnings in 8.40s`

## Fazit

Der nach Run LT dokumentierte Anschluss ist umgesetzt: Die zuvor nur im Summary dokumentierte Drift-Grenze ist nun als wiederverwendbarer, exit-code-fähiger Abnahmecheck für konkrete Batch-Artefakte verfügbar.
