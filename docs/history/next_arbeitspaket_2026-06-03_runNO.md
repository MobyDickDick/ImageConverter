# Nächstes Arbeitspaket – Run NO (2026-06-03)

Dieses Arbeitspaket bearbeitet den nächsten Anschluss aus `docs/open_tasks.md`:
**FP-D4**. Schwerpunkt ist, die noch sichtbaren Nicht-Grün-Signale aus dem
aktuellen Kernlauf nicht nur zu akzeptieren, sondern priorisiert und mit einem
reproduzierbaren Ticket zu dokumentieren.

## 1) Umsetzung

- Der Kernlauf wurde vor der Änderung erneut ausgeführt:
  `PYTHONPATH=vendor/linux-py310/site-packages:. PYENV_VERSION=3.10.20 timeout 300 python -m pytest -q -rs`.
- Ergebnis vor der Triage: `680 passed, 5 warnings`, Exit `0`. Skips/Xfails waren
  im Kernprofil nicht sichtbar.
- Die fünf Warnungen wurden als bekannte PyMuPDF/SWIG-Deprecation-Meldungen
  klassifiziert und in `pytest.ini` mit drei eng passenden `filterwarnings`-
  Einträgen allowlisted.
- `docs/non_green_triage_2026-06-03_runNO.md` dokumentiert Priorität,
  Repro-Befehl, Allowlist-Entscheidung und Recovery-Plan für A4-FU1.
- `docs/test_followup_tasks_2026-05-20.md` und `docs/open_tasks.md` markieren den
  FP-D4-Abschluss und verlinken die neue Triage.

## 2) Grenzen

Die Änderung behebt die externe PyMuPDF/SWIG-Ursache nicht dauerhaft. Die
Allowlist ist bewusst eng auf die drei bekannten Meldungstexte begrenzt. Nach
einem Dependency-Upgrade soll die Allowlist testweise entfernt und der Kernlauf
mit `-W error` geprüft werden.

## 3) Nachweis

- Befehl:
  - `PYTHONPATH=vendor/linux-py310/site-packages:. PYENV_VERSION=3.10.20 timeout 300 python -m pytest -q -rs`
- Ergebnis nach der Allowlist: `680 passed`, Exit `0`, Laufzeit `10.63s`, kein
  Warning-Summary.

## Kurzfazit

FP-D4 ist abgeschlossen: Die aktuelle Nicht-Grün-Liste ist priorisiert, das
verbleibende Kernsignal ist als reproduzierbares A4-FU1-Ticket dokumentiert, und
der Kernlauf läuft nach enger Übergangs-Allowlist ohne sichtbare Warnings durch.
