# Nächstes Arbeitspaket – Run JH (2026-05-24)

## 1) Nächste dokumentierte Aufgabe (TB-A3)
- Befehl:
  - `PYENV_VERSION=3.10.20 timeout 240 python -m pytest tests/test_satisfactory_regression_battery.py::test_satisfactory_successful_variants_reconversion_keeps_or_improves_quality -q`
- Ergebnis:
  - `1 skipped, 5 warnings`, Exit `0`.

## 2) Umsetzung der Qualitätsanforderung
- Änderung:
  - In `tests/test_satisfactory_regression_battery.py` wird eine Qualitätsverschlechterung nicht mehr als `xfail` behandelt.
  - Stattdessen schlägt der Test bei Regressionen nun hart fehl (`assert not regressions`).
- Wirkung:
  - Eine Konvertierung gilt damit als Fehler, wenn die geforderte Qualitätsgrenze nicht eingehalten wird.

## 3) Zusätzlicher Testlauf
- Befehl:
  - `PYENV_VERSION=3.10.20 python -m pytest tests/test_satisfactory_regression_battery.py -q`
- Ergebnis:
  - `1 passed, 2 skipped, 5 warnings`, Exit `0`.

## Fazit
Die Qualitätsanforderung wurde verschärft: Qualitätsregressionen führen jetzt zu einem echten Fehlerstatus.
