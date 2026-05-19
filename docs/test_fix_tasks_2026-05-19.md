# Test-Fix-Aufgabenplan (Stand: 2026-05-19)

## Ergebnis des aktuellen Testlaufs
- Befehl: `pytest -q`
- Status: **fehlgeschlagen bereits in der Test-Collection**.
- Hauptursache: `numpy` kann unter Python **3.12.13** nicht geladen werden, während das Repo ein vendored Wheel-Set für **linux-py310** enthält.

## Beobachtete Fehlerbilder
1. `ModuleNotFoundError: No module named 'numpy'`
2. `No module named 'numpy._core._multiarray_umath'`
3. Folgefehler bei `cv2`, da OpenCV `numpy` benötigt.

## Konkrete Aufgaben, damit wieder alle Tests durchlaufen

### AP-1: Python-/Dependency-Matrix korrigieren (blockierend)
- Ziel: Laufzeit und vendored Binary-Dependencies auf dieselbe Python-Major/Minor-Version bringen.
- To-dos:
  - Entscheiden: **entweder** Testlauf auf Python 3.10 pinnen **oder** Vendor-Ordner für Python 3.12 neu aufbauen.
  - Falls 3.10-Strategie:
    - CI/Local Test-Entrypoint auf 3.10 setzen.
    - Sicherstellen, dass `vendor/linux-py310/site-packages` nur unter 3.10 genutzt wird.
  - Falls 3.12-Strategie:
    - `numpy`, `opencv-python-headless` (und weitere native Pakete) für CPython 3.12 kompatibel bereitstellen.
- Akzeptanzkriterium:
  - `python -c "import numpy, cv2; print(numpy.__version__)"` läuft fehlerfrei.

### AP-2: Fallback-Importlogik absichern
- Ziel: Keine irreführenden Numpy-Fehler beim Laden von vendored Paketen für falsche Python-Version.
- To-dos:
  - In der Import-Fallback-Logik (Dependency-Helper) eine Guard einbauen, die Python-Version gegen Vendor-Pfad validiert.
  - Bei Mismatch: klaren Hinweis mit Lösungspfad ausgeben (z. B. „nutze py310 oder regeneriere vendor für py312“).
- Akzeptanzkriterium:
  - Bei absichtlichem Mismatch kommt eine eindeutige, handlungsorientierte Fehlermeldung.

### AP-3: Tests für optional dependencies robuster machen
- Ziel: Tests, die optionale native Dependencies nutzen, sollen sauber skippen statt mit Collection-Error zu abbrechen.
- To-dos:
  - Detailtests mit direktem `import numpy as np` auf `pytest.importorskip("numpy", exc_type=ImportError)` umstellen, wo fachlich sinnvoll.
  - Dasselbe Muster für `cv2` anwenden.
- Akzeptanzkriterium:
  - Fehlende optionale Pakete führen zu `SKIPPED`, nicht zu `ERROR during collection`.

### AP-4: Vollständige Regression erneut ausführen
- Ziel: Nach AP-1 bis AP-3 grüner Gesamtlauf.
- To-dos:
  - `pytest -q`
  - Bei Bedarf zusätzlich selektive Gruppenläufe (detailtests / shape detection) zur schnelleren Diagnose.
- Akzeptanzkriterium:
  - Keine Collection-Errors, keine Import-Fehler auf `numpy/cv2`.

## Betroffene Testmodule aus dem aktuellen Lauf
- `tests/detailtests/test_composite_svg_helpers.py`
- `tests/detailtests/test_diffing_helpers.py`
- `tests/detailtests/test_element_mask_helpers.py`
- `tests/detailtests/test_error_metric_helpers.py`
- `tests/detailtests/test_gradient_stripe_strategy_helpers.py`
- `tests/detailtests/test_perception_geometry_helpers.py`
- `tests/detailtests/test_remaining_geometry_helpers.py`
- `tests/detailtests/test_semantic_ac0050_helpers.py`
- `tests/detailtests/test_semantic_circle_style_helpers.py`
