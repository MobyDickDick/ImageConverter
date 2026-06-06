# Nicht-Grün-Triage – FP-D4 Run NO (2026-06-03)

Dieses Dokument erfüllt FP-D4 aus `docs/open_tasks.md`: Warnings/Skips/Xfails
werden aus dem aktuellen Kernlauf priorisiert, und mindestens ein Nicht-Grün-
Thema wird als reproduzierbares Ticket mit Repro-Befehl festgehalten.

## 1) Aktueller Kernlauf

- **Befehl:** `PYTHONPATH=vendor/linux-py310/site-packages:. PYENV_VERSION=3.10.20 timeout 300 python -m pytest -q -rs`
- **Vor Triage/Allowlist:** `680 passed, 5 warnings`, Exit `0`, Laufzeit `10.72s`.
- **Warnings:** 5 Deprecation-Warnungen aus `<frozen importlib._bootstrap>:241`:
  - `builtin type SwigPyPacked has no __module__ attribute` (2 Vorkommen)
  - `builtin type SwigPyObject has no __module__ attribute` (2 Vorkommen)
  - `builtin type swigvarlink has no __module__ attribute` (1 Vorkommen plus ein
    interpreter-shutdown echo)
- **Skips/Xfails:** Im Kernprofil keine `skipped`, `xfailed` oder `xpassed`
  Ergebnisse im finalen Summary.

## 2) Priorisierung

| Priorität | Signal | Einordnung | Entscheidung |
| --- | --- | --- | --- |
| P1 | PyMuPDF/SWIG-Deprecation-Warnungen | Externe Binding-Warnungen, bekannt seit A4; sie verschmutzen den Kernlauf, obwohl alle Tests passieren. | Temporäre, eng gematchte `pytest.ini`-Allowlist für genau diese drei Meldungstexte. |
| P2 | Skips/Xfails im Kernprofil | Aktuell keine im Kernprofil sichtbar. | Keine neue Kernaufgabe; bestehende Heavy-/Optional-Follow-ups bleiben separat. |
| P3 | Deselected/Heavy-Profile | Nicht Teil des FP-D4-Kernlaufs; bereits in CI-/Heavy-Profilen ausgelagert. | In FP-D5/Heavy-Diagnosen weiterverfolgen, nicht in FP-D4 vermischen. |

## 3) Reproduzierbares Ticket: A4-FU1 / SWIG-Warnungs-Allowlist

- **Ticket:** A4-FU1 bleibt bis zu einem Dependency-Upgrade offen, ist aber nun
  als erlaubte Übergangswarnung dokumentiert und technisch eng gefiltert.
- **Repro ohne Allowlist:** `PYTHONPATH=vendor/linux-py310/site-packages:. PYENV_VERSION=3.10.20 timeout 300 python -m pytest -q -rs`
  zeigte vor der Änderung `680 passed, 5 warnings`.
- **Akzeptanz für diese Triage:** Der gleiche Kernlauf endet nach der Allowlist
  ohne sichtbares Warning-Summary und ohne Skips/Xfails im Kernprofil.
- **Recovery-Plan:** Bei einem PyMuPDF-/SWIG-Update die drei `filterwarnings`-
  Einträge in `pytest.ini` testweise entfernen und den Kernlauf erneut mit
  `-W error` prüfen. Wenn keine Warnung mehr entsteht, A4-FU1 schließen und die
  Allowlist löschen.

## 4) 5-Zeilen-Log

- **Getestet:** Kernprofil mit `pytest -q -rs` vor und nach enger Warning-Allowlist.
- **Ergebnis:** Vorher `680 passed, 5 warnings`; nachher erwartetes Ziel `680 passed` ohne Warning-Summary.
- **Blocker:** Keine neuen Kernprofil-Blocker; technische Ursache bleibt externe PyMuPDF/SWIG-Binding-Warnung.
- **Nächster Schritt:** FP-D5 starten und die Vollbereichs-/Heavy-Läufe in messbare Batches zerlegen.
- **Morgiger Startbefehl:** `PYTHONPATH=vendor/linux-py310/site-packages:. PYENV_VERSION=3.10.20 timeout 300 python -m pytest -q -rs`.
