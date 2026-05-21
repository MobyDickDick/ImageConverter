# Reproduzierbare Skip-Anleitungen (Stand 2026-05-21)

Diese Anleitung dokumentiert die aktuell im Snapshot sichtbaren Skip-Gründe und wie sie reproduzierbar geprüft bzw. aufgelöst werden.

## 1) Fehlende Baseline-Varianten (`test_satisfactory_regression_battery.py`)

**Skip-Text:** `No baseline variants found...`

**Repro:**
```bash
python -m pytest -q tests/test_satisfactory_regression_battery.py::test_satisfactory_baseline_reconversion_smoke
```

**Auflösung:**
```bash
python -m tools/manage_satisfactory_baseline.py --help
```
Danach Baseline-Artefakte erzeugen und Test erneut ausführen.

## 2) Fehlende optionale Native-Dependencies (`numpy`/`cv2`/`fitz`)

**Skip-Texte:** z. B. `numpy not available in this environment`, `numpy/cv2 not available in this environment`.

**Repro:**
```bash
python -m pytest -q tests/test_image_composite_converter.py -k "numpy or cv2 or fitz"
```

**Auflösung:**
- Python-3.10-Umgebung mit passenden Vendor-/Wheel-Abhängigkeiten verwenden.
- Danach Verifikation:
```bash
python -c "import numpy, cv2; print('ok', numpy.__version__)"
```

## 3) AC08/Fixture-Dateien fehlen

**Skip-Texte:** z. B. `AC08 fixture inputs not available`, `missing regression fixture: ...`.

**Repro:**
```bash
python -m pytest -q tests/test_image_composite_converter.py -k "fixture inputs"
```

**Auflösung:**
- Benötigte Fixtures in `artifacts/images_to_convert` ergänzen.
- Erneuter Einzeltestlauf auf NodeID-Ebene.

## 4) Expliziter Smoke-Task-Placeholder

**Skip-Text:** `AUFGABE: stabilisiere AC0800 smoke output...`

**Repro:**
```bash
python -m pytest -q tests/test_conversion_regression_smoke.py::test_ac08_regression_smoke_run_creates_expected_outputs
```

**Auflösung:**
- Erwartungswerte (SVG/Metric-Drift) stabilisieren.
- Danach `pytest -q` für den Smoke-Test ohne Skip verifizieren.
