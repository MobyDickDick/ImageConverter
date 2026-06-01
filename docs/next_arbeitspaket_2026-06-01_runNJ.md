# Nacharbeit – Satisfactory-Regression-Gate (Run NJ, 2026-06-01)

## Anlass

Die AC0100-Nacharbeit aus Run NI enthielt einen gezielten AC0100-Smoke. Auf die
Rückfrage hin wurde klargestellt: Der Schutz für **alle bisher erfolgreich
konvertierten Bilder** muss explizit als GitHub-delegiertes Gate sichtbar sein.

## Umsetzung

- `tools/run_satisfactory_regression_battery.sh` aktiviert nun selbst
  `RUN_HEAVY_CONVERSION_TESTS=1` und setzt bei vorhandenem Vendor-Bundle den
  `PYTHONPATH`. Damit wird `tests/test_satisfactory_regression_battery.py` nicht
  mehr versehentlich durch das Default-Heavy-Test-Collecting übersprungen.
- `.github/workflows/local-completion-checks.yml` enthält jetzt den separaten Job
  `satisfactory-regression-battery`. Dieser Job führt genau diese Batterie in
  GitHub Actions aus.
- Die bestehende Batterie konvertiert alle Varianten aus
  `artifacts/regression_baseline/satisfactory/variants.txt` erneut und vergleicht
  jede neue `mean_delta2`-Qualität gegen die gespeicherte Baseline. Eine
  Verschlechterung wird als Regression gemeldet.

## Lokaler Befund

- Der vollständige Lauf wurde lokal mit `timeout 240` gestartet, lief aber über
  das lokale Zeitbudget hinaus. Deshalb bleibt der teure Vollnachweis bewusst an
  GitHub Actions delegiert.
- Dokumentations-/Workflow-Tests und ein Skript-Smoke wurden lokal gezielt
  geprüft.
