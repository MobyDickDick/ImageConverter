# Nächstes Arbeitspaket – Run LW (2026-05-29)

Dieses Arbeitspaket bearbeitet den nach Run LV dokumentierten Anschluss: Das Drift-Gate wird zusätzlich in ein ausführbares Sammelskript für lokale Abschlusschecks gebündelt.

## 1) Nächste dokumentierte Aufgabe: ausführbares Abschlussprofil

- Umsetzung:
  - Neues Skript `tools/run_local_completion_checks.sh` bündelt `compileall`, Pytest, CLI-Help-Smoke und den Ketten-Telemetrie-Drift-Gate-Check.
  - Das Skript ergänzt bei vorhandenem `vendor/linux-py310/site-packages` automatisch `PYTHONPATH`, damit der CLI-Smoke die im Repo gebündelten Bild-/Numerik-Abhängigkeiten auflösen kann.
  - Ohne vorhandenes `chain_phase_telemetry_summary.txt` wird der Drift-Gate-Schritt standardmäßig explizit als `SKIP` protokolliert; mit `--require-drift-summary` wird ein fehlendes Summary zum Fehler.
  - `docs/image_converter_workflow.md` und `README.md` verweisen auf das Sammelprofil.
  - `tests/test_image_composite_converter.py::test_local_workflow_doc_tracks_current_commands` sichert den neuen Workflow-Befehl und die Pflicht-Option `--require-drift-summary` ab.

## 2) Sichernde Tests

- Befehl:
  - `PYENV_VERSION=3.10.20 python -m pytest -q tests/test_image_composite_converter.py::test_local_workflow_doc_tracks_current_commands`
- Ergebnis:
  - Exit `0`
  - `1 passed, 5 warnings in 0.66s`
- Log:
  - `artifacts/converted_images/reports/local_completion_profile_doc_test_2026-05-29_runLW.log`

- Befehl:
  - `PYENV_VERSION=3.10.20 timeout 300 ./tools/run_local_completion_checks.sh`
- Ergebnis:
  - Exit `0`
  - `compileall` erfolgreich
  - Pytest vollständig grün: `566 passed, 5 warnings in 5.13s`
  - CLI-Help-Smoke erfolgreich
  - Drift-Gate-Schritt bewusst `SKIP`, weil in diesem Code-/Dokumentationslauf kein `chain_phase_telemetry_summary.txt` erzeugt wurde
- Log:
  - `artifacts/converted_images/reports/local_completion_profile_2026-05-29_runLW.log`

## Fazit

Der nach Run LV dokumentierte Anschluss ist umgesetzt: Das lokale Abschlussprofil ist nun nicht nur dokumentiert, sondern als ausführbares Skript vorhanden und durch gezielten Workflow-Test plus vollständigen Sammellauf abgesichert.
