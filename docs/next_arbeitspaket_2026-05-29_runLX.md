# Nächstes Arbeitspaket – Run LX (2026-05-29)

Dieses Arbeitspaket bearbeitet den nach Run LW dokumentierten Anschluss: Das lokale Abschlussprofil wird in einen automatisierten CI-Aufruf eingehängt.

## 1) Nächste dokumentierte Aufgabe: Abschlussprofil in CI verdrahten

- Umsetzung:
  - Neuer GitHub-Actions-Workflow `.github/workflows/local-completion-checks.yml` startet das dokumentierte Abschlussprofil `./tools/run_local_completion_checks.sh` auf Pull Requests, Pushes auf `main`/`master`/`work` und manuell per `workflow_dispatch`.
  - `docs/image_converter_workflow.md` dokumentiert den CI-Aufruf als eigenen Abschnitt und verweist auf die Workflow-Datei.
  - `README.md` kennzeichnet im zentralen Block **Tests and checks**, dass CI denselben Abschlussbefehl nutzt.
  - `tests/test_image_composite_converter.py::test_local_workflow_doc_tracks_current_commands` sichert ab, dass Workflow-Dokumentation und CI-Datei denselben Sammelbefehl enthalten und die erwarteten CI-Trigger vorhanden sind.

## 2) Sichernder Dokumentationstest

- Befehl:
  - `PYENV_VERSION=3.10.20 python -m pytest -q tests/test_image_composite_converter.py::test_local_workflow_doc_tracks_current_commands`
- Ergebnis:
  - Exit `0`
  - `1 passed, 5 warnings in 4.05s`

## 3) Lokales Abschlussprofil

- Befehl:
  - `PYENV_VERSION=3.10.20 timeout 300 ./tools/run_local_completion_checks.sh`
- Ergebnis:
  - Exit `0`
  - `compileall` erfolgreich
  - Pytest vollständig grün: `566 passed, 5 warnings in 6.35s`
  - CLI-Help-Smoke erfolgreich
  - Drift-Gate-Schritt bewusst `SKIP`, weil in diesem Code-/Dokumentationslauf kein `chain_phase_telemetry_summary.txt` erzeugt wurde

## Fazit

Der nach Run LW dokumentierte Anschluss ist umgesetzt: Das ausführbare lokale Abschlussprofil ist nun auch als CI-Workflow verdrahtet und durch einen Workflow-/Dokumentationstest sowie den vollständigen lokalen Abschlusslauf abgesichert.
