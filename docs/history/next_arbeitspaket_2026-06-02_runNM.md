# Nächstes Arbeitspaket – Run NM (2026-06-02)

Dieses Arbeitspaket setzt den Nutzerwunsch um, möglichst viele Testsignale aus
dem lokalen Abschluss in GitHub Actions zu verlagern. Fachlich schließt es den
nächsten Testhygiene-Anschluss aus `docs/open_tasks.md`: **FP-D3-1**
(Pflicht-Pre-Commit-Checks definieren) ab.

## 1) Umsetzung

- `.github/workflows/local-completion-checks.yml` enthält nun neben dem lokalen
  Abschlussprofil und dem verpflichtenden Drift-Gate zusätzliche CI-Jobs für:
  - die Pytest-Profilmatrix `core-green`/`extended`,
  - die Safe-Baseline,
  - die dokumentierten Regression-Checks,
  - die bereits bestehende Satisfactory-Regressionsbatterie,
  - einen manuellen `workflow_dispatch`-Volljob für
    `tests/test_image_composite_converter.py` mit `RUN_HEAVY_CONVERSION_TESTS=1`.
- Safe-Baseline, Regression-Checks und der Full-Heavy-Job sind zusätzlich durch
  den manuellen `workflow_dispatch`-Input `run_heavy_diagnostics` geschützt. Sie
  setzen bei Aktivierung explizit `RUN_HEAVY_CONVERSION_TESTS=1`, blockieren aber
  nicht mehr automatisch jeden Pull Request.
- `docs/image_converter_workflow.md` und `README.md` dokumentieren die neue
  Aufteilung: schnelle lokale Abschlusschecks bleiben lokal spiegelbar, längere
  Profil-/Regression-/Heavy-Batterien laufen primär in GitHub Actions.
- Der Workflow-Dokumentationstest prüft die neuen Jobnamen, Kommandos,
  Heavy-Env-Gates und den manuellen Volljob.

## 2) Grenzen

Die bekannten schweren Konvertierungsdiagnosen werden bewusst nur manuell per
`workflow_dispatch` mit aktiviertem `run_heavy_diagnostics` gestartet. Dadurch
sind sie nach GitHub ausgelagert, blockieren aber Pull Requests nicht
automatisch, solange die T6-/TB1-Langläuferhistorie nicht vollständig abgebaut
ist.

## 3) Nachweis

Gezielter Workflow-Dokumentationstest:

- Befehl:
  - `PYTHONPATH=. pytest -q tests/test_image_composite_converter.py::test_local_workflow_doc_tracks_current_commands`
- Ergebnis nach Opt-in-Korrektur: `1 passed, 5 warnings`, Exit `0`, Laufzeit `2.11s`.

Tooltests für das lokale Abschlussprofil:

- Befehl:
  - `PYTHONPATH=. pytest -q tests/detailtests/test_local_completion_checks_tool.py`
- Ergebnis: `2 passed`, Exit `0`, Laufzeit `0.21s`.

Pytest-Profilmatrix lokal gespiegelt:

- Befehl:
  - `python tools/run_pytest_profile.py core-green`
- Ergebnis: `24 passed`, Exit `0`, Laufzeit `0.28s`.
- Befehl:
  - `python tools/run_pytest_profile.py extended`
- Ergebnis: `676 passed, 5 warnings`, Exit `0`, Laufzeit `11.60s`.

Shell-Syntaxprüfung der dokumentierten Runner:

- Befehl:
  - `bash -n tools/run_local_completion_checks.sh tools/run_regression_checks.sh tools/run_safe_test_baseline.sh tools/run_satisfactory_regression_battery.sh`
- Ergebnis: Exit `0`.

Workflow-Strukturprüfung:

- Befehl:
  - `ruby -e 'require "yaml"; YAML.load_file(".github/workflows/local-completion-checks.yml"); puts "yaml ok"'`
- Ergebnis: `yaml ok`, Exit `0`.
- Befehl:
  - `python - <<'PY' ... workflow opt-in tokens ok ... PY`
- Ergebnis: `workflow opt-in tokens ok`, Exit `0`.

## Kurzfazit

FP-D3-1 ist abgeschlossen: Das Pflicht-Gate ist dokumentiert, per Test gegen
Workflow-/Doku-Drift gesichert und die längeren Checks sind soweit sinnvoll nach
GitHub Actions ausgelagert. Die bekannten Heavy-Langläufer bleiben als manuell
per `run_heavy_diagnostics` auslösbare GitHub-Jobs vom automatischen PR-Gate
getrennt.
