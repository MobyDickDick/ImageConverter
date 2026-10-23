# Nächstes Arbeitspaket – Run LZ (2026-05-29)

Dieses Arbeitspaket bearbeitet den nach Run LY dokumentierten Anschluss: Der
separate CI-Job für das verpflichtende Drift-Summary erhält dieselbe
Testabhängigkeits-Initialisierung wie das normale Abschlussprofil.

## 1) Nächste dokumentierte Aufgabe: CI-Pflichtjob vollständig bootstrappen

- Umsetzung:
  - `.github/workflows/local-completion-checks.yml` installiert nun auch im Job
    `batch-artifact-drift-gate` vor dem Abschlussprofil `pytest`.
  - `docs/image_converter_workflow.md` dokumentiert, dass der Pflichtjob seine
    Testabhängigkeit ebenfalls initialisiert, bevor er das repräsentative
    `chain_phase_telemetry_summary.txt` anlegt, und führt die zuvor
    getestete `--summary`-Option im lokalen Profilabschnitt wieder explizit auf.
  - `README.md` kennzeichnet im zentralen Block **Tests and checks**, dass der
    Pflichtjob neben dem Drift-Summary-Gate ebenfalls `pytest` installiert.
  - `tests/test_image_composite_converter.py::test_local_workflow_doc_tracks_current_commands`
    sichert ab, dass der CI-Workflow die `pytest`-Installation für beide Jobs
    enthält.

## 2) Sichernder Dokumentationstest

- Befehl:
  - `PYENV_VERSION=3.10.20 python -m pytest -q tests/test_image_composite_converter.py::test_local_workflow_doc_tracks_current_commands`
- Ergebnis:
  - Exit `0`
  - `1 passed, 5 warnings in 0.85s`

## 3) Lokales Abschlussprofil

- Befehl:
  - `PYENV_VERSION=3.10.20 timeout 300 ./tools/run_local_completion_checks.sh`
- Ergebnis:
  - Exit `0`
  - `compileall` erfolgreich
  - Pytest vollständig grün: `566 passed, 5 warnings in 7.45s`
  - CLI-Help-Smoke erfolgreich
  - Drift-Gate-Schritt bewusst `SKIP`, weil in diesem Code-/Dokumentationslauf kein
    `chain_phase_telemetry_summary.txt` vorhanden war

## Fazit

Der nach Run LY dokumentierte Anschluss ist umgesetzt: Beide CI-Jobs bootstrappen
nun ihre Pytest-Abhängigkeit explizit, sodass sowohl das normale Abschlussprofil
als auch der verpflichtende Drift-Summary-Pfad auf einem frischen GitHub-Actions-
Runner denselben Testbefehl starten können.
