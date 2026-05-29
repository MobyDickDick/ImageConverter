# Nächstes Arbeitspaket – Run LV (2026-05-29)

Dieses Arbeitspaket bearbeitet den nach Run LU dokumentierten Anschluss: Der neue Drift-Artefakt-Check wird in das dokumentierte Gate-/Pre-Commit-Profil aufgenommen.

## 1) Nächste dokumentierte Aufgabe: Drift-Gate im lokalen Abschlussprofil

- Aktualisiert:
  - `docs/image_converter_workflow.md` enthält nun einen eigenen Abschnitt **Ketten-Telemetrie-Drift-Gate prüfen**.
  - `README.md` listet den Drift-Gate-Check im zentralen Block **Tests and checks**.
  - `tests/test_image_composite_converter.py::test_local_workflow_doc_tracks_current_commands` sichert ab, dass der Workflow den Drift-Gate-Befehl weiterhin dokumentiert.
- Dokumentierter Befehl:
  - `python tools/check_chain_telemetry_drift_gate.py artifacts/converted_images/reports/chain_phase_telemetry_summary.txt`
- Verhalten:
  - `drift_status=pass` wird als Exit `0` akzeptiert.
  - Warnungen, fehlende Artefakte oder fehlender `drift_status` bleiben Exit `1` mit stabilen Reason-Codes.

## 2) Sichernde Dokumentations-/Detailtest-Probe

- Befehl:
  - `PYENV_VERSION=3.10.20 python -m pytest -q tests/test_image_composite_converter.py::test_local_workflow_doc_tracks_current_commands`
- Ergebnis:
  - Exit `0`
  - `1 passed, 5 warnings in 3.91s`

## 3) Drift-Gate-Probe mit Pass-Artefakt

- Befehl:
  - `tmpdir=$(mktemp -d); printf 'drift_status=pass\ndrift_reasons=\n' > "$tmpdir/chain_phase_telemetry_summary.txt"; python tools/check_chain_telemetry_drift_gate.py "$tmpdir/chain_phase_telemetry_summary.txt"; status=$?; rm -rf "$tmpdir"; exit $status`
- Ergebnis:
  - Exit `0`
  - `PASS chain telemetry drift gate: .../chain_phase_telemetry_summary.txt`

## 4) Volltest

- Befehl:
  - `PYENV_VERSION=3.10.20 timeout 300 python -m pytest -q -rs`
- Ergebnis:
  - Exit `0`
  - `566 passed, 5 warnings in 6.18s`

## Fazit

Der nach Run LU dokumentierte Anschluss ist umgesetzt: Der automatisierte Drift-Artefakt-Check ist nicht mehr nur als Tool vorhanden, sondern als verbindlicher lokaler Workflow-/Gate-Baustein dokumentiert und durch einen bestehenden Workflow-Dokumentationstest abgesichert.
