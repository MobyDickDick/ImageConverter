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
- Safe-Baseline und Regression-Checks setzen in GitHub Actions explizit
  `RUN_HEAVY_CONVERSION_TESTS=1`, damit ausgelagerte Konvertierungsregressionen
  nicht vom lokalen Default-Skip-Gate verdeckt werden.
- `docs/image_converter_workflow.md` und `README.md` dokumentieren die neue
  Aufteilung: schnelle lokale Abschlusschecks bleiben lokal spiegelbar, längere
  Profil-/Regression-/Heavy-Batterien laufen primär in GitHub Actions.
- Der Workflow-Dokumentationstest prüft die neuen Jobnamen, Kommandos,
  Heavy-Env-Gates und den manuellen Volljob.

## 2) Grenzen

Die bekannte schwere `tests/test_image_composite_converter.py`-Vollprüfung wird
bewusst nur manuell per `workflow_dispatch` gestartet. Dadurch ist sie nach
GitHub ausgelagert, blockiert aber Pull Requests nicht automatisch, solange die
T6-/TB1-Langläuferhistorie nicht vollständig abgebaut ist.

## 3) Nachweis

Gezielter Workflow-Dokumentationstest:

- Befehl:
  - `PYTHONPATH=. pytest -q tests/test_image_composite_converter.py::test_local_workflow_doc_tracks_current_commands`
- Ergebnis: `1 passed, 5 warnings`, Exit `0`, Laufzeit `5.47s`.

Tooltests für das lokale Abschlussprofil:

- Befehl:
  - `PYTHONPATH=. pytest -q tests/detailtests/test_local_completion_checks_tool.py`
- Ergebnis: `2 passed`, Exit `0`, Laufzeit `0.29s`.

Pytest-Profilmatrix lokal gespiegelt:

- Befehl:
  - `python tools/run_pytest_profile.py core-green`
- Ergebnis: `24 passed`, Exit `0`, Laufzeit `0.38s`.
- Befehl:
  - `python tools/run_pytest_profile.py extended`
- Ergebnis: `676 passed, 5 warnings`, Exit `0`, Laufzeit `11.60s`.

Shell-Syntaxprüfung der dokumentierten Runner:

- Befehl:
  - `bash -n tools/run_local_completion_checks.sh tools/run_regression_checks.sh tools/run_safe_test_baseline.sh tools/run_satisfactory_regression_battery.sh`
- Ergebnis: Exit `0`.

## Kurzfazit

FP-D3-1 ist abgeschlossen: Das Pflicht-Gate ist dokumentiert, per Test gegen
Workflow-/Doku-Drift gesichert und die längeren Checks sind soweit sinnvoll nach
GitHub Actions ausgelagert. Nur der bekannte Voll-Heavy-Langläufer bleibt als
manuell auslösbarer GitHub-Job vom automatischen PR-Gate getrennt.
