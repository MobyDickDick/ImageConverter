# Nächstes Arbeitspaket – Run NN (2026-06-03)

Dieses Arbeitspaket schließt den nächsten Anschluss aus `docs/open_tasks.md` ab:
**FP-D3-2** und damit **FP-D3-EXIT**. Schwerpunkt ist, den bereits nach GitHub
Actions ausgelagerten Pflicht-Abschluss so zu erweitern, dass pro Commit nicht
nur ein Jobstatus, sondern auch ein auswertbarer Testnachweis (`PASS`/`FAIL`,
Exit-Code und Log) als GitHub-Artefakt vorliegt.

## 1) Umsetzung

- `tools/run_test_evidence.sh` ergänzt einen generischen Wrapper für Testbefehle:
  Er spiegelt die Befehlsausgabe in eine Logdatei, schreibt eine Markdown-
  Zusammenfassung mit `PASS`/`FAIL`, Exit-Code, Git-Ref/SHA und Logpfad und gibt
  anschließend den Original-Exit-Code des Befehls zurück.
- `.github/workflows/local-completion-checks.yml` startet das dokumentierte
  lokale Abschlussprofil im Job `completion-profile` nun über diesen Wrapper und
  lädt `artifacts/test-evidence` immer als Artefakt
  `completion-profile-test-evidence` hoch.
- `docs/image_converter_workflow.md` und `README.md` dokumentieren, dass der
  Pflicht-Testnachweis pro Pull-Request-/Push-Commit in GitHub Actions erzeugt
  wird. Die längeren Profile bleiben wie im vorherigen Arbeitspaket in separate
  GitHub-Jobs ausgelagert.
- Der bestehende Workflow-Dokumentationstest prüft den neuen Evidence-Wrapper,
  die Artefaktpfade und den Upload. Zusätzlich sichern Tooltests die
  `PASS`- und `FAIL`-Zusammenfassungen des Wrappers ab.
- `docs/open_tasks.md` markiert **FP-D3-2** und **FP-D3-EXIT** als erledigt.

## 2) Grenzen

Der Wrapper protokolliert aktuell den Pflichtabschlussjob `completion-profile`.
Die bereits ausgelagerten Zusatzjobs behalten ihre eigenen GitHub-Logs und
Artefakte; für diese Jobs wurde bewusst keine zusätzliche Wrapper-Duplizierung
eingeführt, damit die CI-Laufzeit und Jobstruktur schlank bleibt.

## 3) Nachweis

Gezielte Wrapper-/Tooltests:

- Befehl:
  - `PYTHONPATH=. pytest -q tests/detailtests/test_local_completion_checks_tool.py`
- Ergebnis: `4 passed`, Exit `0`, Laufzeit `0.52s`.

Workflow-Dokumentationstest:

- Befehl:
  - `PYTHONPATH=. pytest -q tests/test_image_composite_converter.py::test_local_workflow_doc_tracks_current_commands`
- Ergebnis: `1 passed, 5 warnings`, Exit `0`, Laufzeit `4.49s`.

Shell-/Workflow-Syntaxprüfung:

- Befehl:
  - `bash -n tools/run_test_evidence.sh && bash -n tools/run_local_completion_checks.sh`
- Ergebnis: Exit `0`.
- Befehl:
  - `ruby -e 'require "yaml"; YAML.load_file(".github/workflows/local-completion-checks.yml"); puts "yaml ok"'`
- Ergebnis: `yaml ok`, Exit `0`.

## Kurzfazit

FP-D3 ist abgeschlossen: Der Pflichtabschluss läuft weiterhin in GitHub Actions,
und jeder Commit erhält dort automatisch ein Artefakt mit Testausgabe,
`PASS`/`FAIL`-Bewertung und Exit-Code. Lokale Läufe können denselben Nachweis
über `tools/run_test_evidence.sh` reproduzieren.
