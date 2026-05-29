# Nächstes Arbeitspaket – Run LY (2026-05-29)

Dieses Arbeitspaket bearbeitet den nach Run LX dokumentierten Anschluss: Das CI-Profil erhält eine explizite Pflicht-Drift-Probe mit `--require-drift-summary`.

## 1) Nächste dokumentierte Aufgabe: CI-Pflichtpfad für Drift-Summaries

- Umsetzung:
  - `.github/workflows/local-completion-checks.yml` führt nach dem regulären lokalen Abschlussprofil eine zusätzliche Drift-Summary-Probe aus.
  - Die Probe erzeugt im CI-Temp-Verzeichnis ein synthetisches `chain_phase_telemetry_summary.txt` mit `drift_status=pass` und startet dasselbe Abschlussprofil mit `--summary ... --require-drift-summary`.
  - `docs/image_converter_workflow.md` dokumentiert diesen Pflichtpfad als Teil des automatisierten CI-Aufrufs.
  - `README.md` ergänzt den Checkblock um den expliziten `--summary ... --require-drift-summary`-Aufruf.
  - `tests/test_image_composite_converter.py::test_local_workflow_doc_tracks_current_commands` sichert ab, dass Workflow-Dokumentation und CI-Datei den Pflichtpfad inklusive synthetischem Pass-Summary enthalten.

## 2) Sichernder Dokumentationstest

- Befehl:
  - `PYENV_VERSION=3.10.20 python -m pytest -q tests/test_image_composite_converter.py::test_local_workflow_doc_tracks_current_commands`
- Ergebnis:
  - Exit `0`
  - `1 passed, 5 warnings in 3.19s`

## 3) Lokales Abschlussprofil mit verpflichtendem Drift-Summary

- Befehl:
  - `tmpdir=$(mktemp -d); printf 'drift_status=pass\ndrift_reasons=\n' > "$tmpdir/chain_phase_telemetry_summary.txt"; PYENV_VERSION=3.10.20 timeout 300 ./tools/run_local_completion_checks.sh --summary "$tmpdir/chain_phase_telemetry_summary.txt" --require-drift-summary; status=$?; rm -rf "$tmpdir"; exit $status`
- Ergebnis:
  - Exit `0`
  - `compileall` erfolgreich
  - Pytest vollständig grün
  - CLI-Help-Smoke erfolgreich
  - Drift-Gate-Schritt akzeptiert das synthetische Pass-Summary mit `PASS chain telemetry drift gate`

## Fazit

Der nach Run LX dokumentierte Anschluss ist umgesetzt: Der CI-Pfad prüft jetzt nicht nur das Standard-Abschlussprofil, sondern zusätzlich den verpflichtenden Drift-Summary-Modus, der für echte Batch-Artefakt-Jobs fehlende Telemetrie-Summaries hart fehlschlagen lässt.
