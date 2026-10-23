# Nächstes Arbeitspaket – Run LY (2026-05-29)

Dieses Arbeitspaket bearbeitet den nach Run LX dokumentierten Anschluss: Das CI-Profil wird um einen separaten Batch-Artefakt-Job mit verpflichtendem Drift-Summary erweitert.

## 1) Nächste dokumentierte Aufgabe: CI-Drift-Summary verpflichtend prüfen

- Umsetzung:
  - `.github/workflows/local-completion-checks.yml` enthält nun zusätzlich den Job `batch-artifact-drift-gate`.
  - Der Job legt ein repräsentatives `artifacts/converted_images/reports/chain_phase_telemetry_summary.txt` mit `drift_status=pass` an.
  - Danach startet der Job dasselbe Abschlussprofil mit `./tools/run_local_completion_checks.sh --require-drift-summary`, sodass die Pflichtvariante des Drift-Artefakt-Gates in CI abgesichert ist.
  - `docs/image_converter_workflow.md` dokumentiert den separaten CI-Job und den Pflichtaufruf.
  - `README.md` nennt den verpflichtenden Drift-Summary-Aufruf im zentralen Checkblock.
  - `tests/test_image_composite_converter.py::test_local_workflow_doc_tracks_current_commands` prüft, dass der CI-Workflow den separaten Job, das repräsentative Pass-Summary und den Pflichtaufruf enthält.

## 2) Sichernder Dokumentationstest

- Befehl:
  - `PYENV_VERSION=3.10.20 python -m pytest -q tests/test_image_composite_converter.py::test_local_workflow_doc_tracks_current_commands`
- Ergebnis:
  - Exit `0`
  - `1 passed, 5 warnings in 3.78s`

## 3) Lokales Abschlussprofil

- Befehl:
  - `PYENV_VERSION=3.10.20 timeout 300 ./tools/run_local_completion_checks.sh`
- Ergebnis:
  - Exit `0`
  - `compileall` erfolgreich
  - Pytest vollständig grün: `566 passed, 5 warnings in 6.26s`
  - CLI-Help-Smoke erfolgreich
  - Drift-Gate-Schritt bewusst `SKIP`, weil in diesem Code-/Dokumentationslauf kein `chain_phase_telemetry_summary.txt` vorhanden war

## 4) Pflicht-Drift-Summary-Probe

- Befehl:
  - `tmpdir=$(mktemp -d); mkdir -p "$tmpdir/reports"; printf 'drift_status=pass\ndrift_reasons=\n' > "$tmpdir/reports/chain_phase_telemetry_summary.txt"; PYENV_VERSION=3.10.20 timeout 300 ./tools/run_local_completion_checks.sh --summary "$tmpdir/reports/chain_phase_telemetry_summary.txt" --require-drift-summary; status=$?; rm -rf "$tmpdir"; exit $status`
- Ergebnis:
  - Exit `0`
  - `compileall` erfolgreich
  - Pytest vollständig grün: `566 passed, 5 warnings in 5.00s`
  - CLI-Help-Smoke erfolgreich
  - Drift-Gate akzeptiert das synthetische Pass-Summary

## Fazit

Der nach Run LX dokumentierte Anschluss ist umgesetzt: Neben dem normalen CI-Abschlussprofil existiert nun ein separater CI-Job, der den verpflichtenden Drift-Summary-Pfad mit `--require-drift-summary` ausführt und dadurch die Batch-Artefakt-Abnahme explizit gegen fehlende Drift-Summaries schützt.
