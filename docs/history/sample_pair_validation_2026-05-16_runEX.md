# Arbeitspaket Run EX (N5 + Plan-B + nächstes CSV-Bild) — 2026-05-16

## Definition „nächstes Arbeitspaket"

Ab dieser Session bedeutet **„das nächste Arbeitspaket“** verbindlich immer die Kombination aus:

1. **nächste dokumentierte Aufgabe** aus `docs/open_tasks.md` (in der priorisierten Reihenfolge),
2. **eine gekoppelte Plan-B-Aufgabe**,
3. **dem nächsten Bild** aus `artifacts/converted_images/reports/summaries/not_satisfactory_converted_images.csv`.

## 1) Nächste dokumentierte Aufgabe

- Aufgabe: `N5` (Sample-Pair-Validierung als mittlerer Kurzbatch).
- Kommando:
  - `PYENV_VERSION=3.10.20 python -m tools.validate_sample_pairs artifacts/images_to_convert/samples --reference-dir artifacts/images_to_convert --report-csv artifacts/converted_images/reports/sample_pair_validation_2026-05-16_runEX.csv`
- Ergebnis:
  - CSV-Report: `artifacts/converted_images/reports/sample_pair_validation_2026-05-16_runEX.csv`
  - Log: `artifacts/converted_images/reports/sample_pair_validation_2026-05-16_runEX.log`
  - Exit-Code: `0`

## 2) Plan-B-Aufgabe

- Aufgabe: synthetische Plan-B-Probe für die gekoppelte Variante `AC0020_M`.
- Kommando:
  - `PYENV_VERSION=3.10.20 python -m tools.plan_b_synthetic_probe "Bildbeschreibung: Kreis mit horizontalem Griff links; der Griff liegt auf der horizontalen Symmetrieachse des Kreises und läuft teilweise hinter die Kreisscheibe. In der Kreisscheibe steht die Beschriftung m." --variant AC0020_M --output-dir artifacts/converted_images/reports`
- Ergebnis:
  - Log: `artifacts/converted_images/reports/AC0020_M_planb_synthetic_2026-05-16_runEX.log`
  - Exit-Code: `0`

## 3) Nächstes Bild aus CSV

- Quelle: `artifacts/converted_images/reports/summaries/not_satisfactory_converted_images.csv`
- Nächstes Bild nach den bereits bearbeiteten Sample-Markern (`AC0010`, `AC0011`, `AC0020_L`) ist: **`AC0020_M`**.
- Dieses Bild wurde im selben Arbeitspaket über die Plan-B-Probe direkt mitbearbeitet.
