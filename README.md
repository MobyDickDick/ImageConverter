# ImageConverter

ImageConverter converts badge/source images into composite SVG outputs and also
provides annotation/debugging helpers for the source raster files.

## Main entry point

Run the converter via:

```bash
python -m src.imageCompositeConverter
```

The detailed CLI reference lives in [docs/image_converter_cli.md](docs/image_converter_cli.md).
The recommended local verification workflow lives in
[docs/image_converter_workflow.md](docs/image_converter_workflow.md).

## Repository layout

- `src/imageCompositeConverter.py` — converter implementation and CLI.
- `tests/test_imageCompositeConverter.py` — regression tests for the converter.
- `docs/image_converter_cli.md` — command reference.
- `docs/image_converter_workflow.md` — local verification workflow.
- `docs/ac08_improvement_plan.md` — AC08 improvement backlog/history.
- `docs/ac08_artifact_analysis.md` — AC08 artifact analysis notes.
- `docs/open_tasks.md` — current ImageConverter task list.
- `docs/Forms.md` — formal forms model (circle + handle) with constraints and orientations.

## Quick start

### Convert images into SVG outputs

```bash
python -m src.imageCompositeConverter \
  artifacts/images_to_convert \
  --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml \
  --output-dir artifacts/converted_images \
  --start AC0000 \
  --end ZZ9999
```

Wenn einzelne Bilder im Batch nicht vektorisierbar sind, läuft die Konvertierung
weiter und schreibt die Details nach
`artifacts/converted_images/reports/batch_failure_summary.csv`. Der CLI-Prozess
endet in diesem Fall standardmäßig trotzdem mit Exitcode `0`; für CI-/Gate-Läufe,
die bei solchen Einzelfehlern abbrechen sollen, kann `--fail-on-batch-failures`
gesetzt werden.

### Qualitätsparameter für als gut markierte Konvertierungen

```bash
python -m src.successful_conversion_quality_app
```

Die kleine Anwendung liest `artifacts/converted_images/reports/successful_conversions.txt` als Bestenliste, ergänzt die dort bereits als erfolgreich markierten Varianten automatisch um Qualitätskennzahlen wie `total_delta2 = Σ((ΔR)^2 + (ΔG)^2 + (ΔB)^2)`, `mean_delta2` und `std_delta2` und übernimmt neue Konvertierungen nur dann in Manifest und Snapshot, wenn sich mindestens eine Kernmetrik verbessert. Schlechtere Neu-Konvertierungen werden verworfen und – falls vorhanden – aus der gespeicherten Bestenlisten-Sicherung wiederhergestellt. Zusätzlich wird eine sortierte CSV-Bestenliste unter `artifacts/converted_images/reports/successful_conversions.csv` erzeugt bzw. aktualisiert; die Einträge sind nach dem Namen der konvertierten Bilder (`variant`) geordnet.


### Weak-Family-Pipeline (Top-N + Vorher/Nachher)

```bash
python -m src.weak_family_pipeline \
  --before-ranking artifacts/converted_images/reports/pixel_delta2_ranking.csv \
  --top-n 10 \
  --prefix AC08 \
  --selection-out artifacts/converted_images/reports/weak_family_top10.txt
```

Optional kann ein Konverter-Lauf angestoßen und danach eine Vorher/Nachher-CSV geschrieben werden:

```bash
python -m src.weak_family_pipeline \
  --before-ranking artifacts/converted_images/reports/pixel_delta2_ranking_before.csv \
  --after-ranking artifacts/converted_images/reports/pixel_delta2_ranking_after.csv \
  --top-n 10 \
  --prefix AC08 \
  --selection-out artifacts/converted_images/reports/weak_family_top10.txt \
  --comparison-out artifacts/converted_images/reports/weak_family_top10_comparison.csv \
  --run-command "echo Running converter for variants in {variants_file}"
```

`{variants_file}` wird dabei automatisch durch die erzeugte Top-N-Liste ersetzt.

### Inkscape-SVG automatisch bereinigen

```bash
python tools/strip_inkscape_svg.py artifacts/images_to_convert/samples/AC0120_L.svg --in-place
```

Optional statt `--in-place` mit `--output <datei.svg>` in eine neue Datei schreiben.

### Annotate source images

```bash
python -m src.imageCompositeConverter \
  --mode annotate \
  --output-dir artifacts/annotated_images \
  --start AC0811 \
  --end AC0814
```

## Tests and checks

```bash
python -m compileall src tests
python -m pytest
./tools/run_regression_checks.sh
./tools/run_safe_test_baseline.sh
./tools/run_local_completion_checks.sh
# CI nutzt denselben Abschlussbefehl in .github/workflows/local-completion-checks.yml
# und protokolliert Testausgabe + PASS/FAIL pro Commit als GitHub-Artefakt:
./tools/run_test_evidence.sh --name completion-profile --log artifacts/test-evidence/completion-profile.log --summary artifacts/test-evidence/completion-profile-summary.md -- ./tools/run_local_completion_checks.sh
# Zusätzliche GitHub-Jobs lagern Profile aus:
python tools/run_pytest_profile.py core-green
python tools/run_pytest_profile.py extended
# Bekannte Heavy-Diagnosen laufen in GitHub nur mit workflow_dispatch + run_heavy_diagnostics:
RUN_HEAVY_CONVERSION_TESTS=1 ./tools/run_safe_test_baseline.sh
RUN_HEAVY_CONVERSION_TESTS=1 ./tools/run_regression_checks.sh
# Der CI-Job batch-artifact-drift-gate installiert ebenfalls pytest und erzwingt zusätzlich ein vorhandenes Drift-Summary:
./tools/run_local_completion_checks.sh --require-drift-summary
python tools/manage_satisfactory_baseline.py
./tools/run_satisfactory_regression_battery.sh
# Der manuelle GitHub-Job full-heavy-conversion-suite startet bei Bedarf mit run_heavy_diagnostics:
RUN_HEAVY_CONVERSION_TESTS=1 python -m pytest -q -rs tests/test_image_composite_converter.py
# Die Satisfactory-Batterie konvertiert alle in artifacts/regression_baseline/satisfactory/variants.txt
# gespeicherten erfolgreichen Varianten erneut und vergleicht die neue mean_delta2-Qualität
# streng gegen die dort gespeicherten Baseline-SVGs. Jede Verschlechterung schlägt den Test fehl.
python -m src.imageCompositeConverter --help
python tools/check_vendored_cv2.py
python -m src.imageCompositeConverter artifacts/images_to_convert --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --ac08-regression-set --output-dir artifacts/converted_images
python tools/check_chain_telemetry_drift_gate.py artifacts/converted_images/reports/chain_phase_telemetry_summary.txt
python - <<'PY'
from pathlib import Path
import csv
import sys

metrics = {}
with Path("artifacts/converted_images/reports/ac08_success_metrics.csv").open("r", encoding="utf-8", newline="") as f:
    for row in csv.DictReader(f, delimiter=";"):
        metrics[row["metric"]] = row["value"]
failed = [name for name in ("criterion_no_new_batch_aborts", "criterion_no_accepted_regressions", "criterion_validation_rounds_recorded", "criterion_regression_set_improved", "criterion_stable_families_not_worse", "overall_success") if metrics.get(name, "0") != "1"]
print("AC08-Gate:", "PASS" if not failed else "FAIL")
sys.exit(0 if not failed else 1)
PY
# neue erfolgreich konvertierte Bild-IDs in artifacts/converted_images/reports/successful_conversions.txt eintragen; Qualitätswerte werden danach automatisch an diese Einträge ergänzt
```

## VS Code / Windows troubleshooting

Wenn VS Code beim Starten mit `debugpy` einen Fehler wie `Couldn't spawn debuggee: [WinError 5] Zugriff verweigert` meldet und in der geloggten `Command line` nur der Ordner `...\.venv\Scripts` statt `...\.venv\Scripts\python.exe` auftaucht, ist meist der Python-Interpreter falsch ausgewählt.

- Wähle in VS Code über `Python: Select Interpreter` explizit die Datei `.venv\Scripts\python.exe` aus — **nicht** den Ordner `.venv\Scripts`.
- Verwende bevorzugt die mitgelieferte Debug-Konfiguration `ImageConverter: convert interactive range`; sie startet den Einstiegspunkt als Modul (`python -m src.imageCompositeConverter`) und setzt das Workspace-Verzeichnis korrekt.
- Falls du lieber direkt im Terminal prüfst, funktioniert derselbe Start auch ohne Debugger mit `python -m src.imageCompositeConverter artifacts/images_to_convert --interactive-range`.


## Testprofile

Feste Testprofile können über `tools/run_pytest_profile.py` gestartet werden:

- `core-green`: harte grüne Kernbatterie ohne `blocking_conversion`/`optional_fixture`-Marker
- `extended`: breitere Suite ohne `blocking_conversion`
- `research`: nur experimentelle/blockierende Tests

Beispiele:

```bash
python tools/run_pytest_profile.py core-green
python tools/run_pytest_profile.py extended tests/test_image_composite_converter.py -k ac08
python tools/run_pytest_profile.py research
```
