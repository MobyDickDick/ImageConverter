# ImageConverter workflow

Diese Kurzanleitung bündelt die aktuell empfohlenen lokalen Befehle für den
ImageConverter.

## Verbindlicher Abschluss je Aufgabe

Um zu vermeiden, dass bei Neuerungen einzelne Aspekte verschlechtert werden,
wird vor Abschluss **jeder** Aufgabe mindestens der vollständige Check-Block aus
Schritt 1 ausgeführt. Bei Änderungen an der Konvertierungslogik sollten
zusätzlich die Regression-Checks aus Schritt 3 und Schritt 4 laufen.

## 1. Syntax- und Test-Checks

```bash
python -m compileall src tests
python -m pytest
python -m src.imageCompositeConverter --help
```

## 2. Interaktive Konvertierung

```bash
python -m src.imageCompositeConverter \
  artifacts/images_to_convert \
  --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml \
  --interactive-range
```

## 3. Regression-Set für AC08 und Schutz der bereits guten Varianten

```bash
python -m src.imageCompositeConverter \
  artifacts/images_to_convert \
  --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml \
  --ac08-regression-set \
  --output-dir artifacts/converted_images
```

Dabei werden die bereits als gut markierten Varianten aus `artifacts/converted_images/reports/successful_conversions.txt` immer mitgeprüft. Die Datei darf beliebige Bild-IDs enthalten. Für AC08 wird daraus automatisch nur der AC08-Teil in das feste Regression-Set und in die Preservation-Checks übernommen. Wenn eine dieser Varianten nicht mehr `semantic_ok` ist, gilt die Anpassung nicht als erfolgreich und muss vor dem nächsten Schritt korrigiert oder verworfen werden.
Der Lauf gibt außerdem das AC08-Success-Gate direkt in der Konsole als
`[INFO] AC08 success gate passed ...` oder `[WARN] AC08 success gate failed ...`
aus, inklusive der fehlgeschlagenen Kriterien und
`mean_validation_rounds_per_file`.

## 4. AC08-Success-Gate als expliziter Regression-Check (CI-/Shell-tauglich)

```bash
python - <<'PY'
from pathlib import Path
import csv
import sys

metrics_path = Path("artifacts/converted_images/reports/ac08_success_metrics.csv")
if not metrics_path.exists():
    raise SystemExit("ac08_success_metrics.csv fehlt – zuerst --ac08-regression-set ausführen.")

metrics = {}
with metrics_path.open("r", encoding="utf-8", newline="") as f:
    for row in csv.DictReader(f, delimiter=";"):
        metrics[row["metric"]] = row["value"]

required = (
    "criterion_no_new_batch_aborts",
    "criterion_no_accepted_regressions",
    "criterion_validation_rounds_recorded",
    "criterion_regression_set_improved",
    "criterion_stable_families_not_worse",
    "overall_success",
)
failed = [name for name in required if metrics.get(name, "0") != "1"]
print("AC08-Gate:", "PASS" if not failed else "FAIL")
if failed:
    print("Fehlgeschlagene Kriterien:", ", ".join(failed))
    sys.exit(1)
PY
```

## 5. Ketten-Telemetrie-Drift-Gate prüfen

Nach Batchläufen, die `chain_phase_telemetry_summary.txt` erzeugen, ist die
konfigurierte Drift-Grenze als eigener, Shell-/CI-tauglicher Gate-Check
auszuführen:

```bash
python tools/check_chain_telemetry_drift_gate.py artifacts/converted_images/reports/chain_phase_telemetry_summary.txt
```

Der Check akzeptiert nur ein Summary mit `drift_status=pass` und beendet sich
dann mit Exit `0`. Warnungen, fehlende Artefakte oder ein fehlender
`drift_status` liefern Exit `1` mit stabilen Reason-Codes, damit
Batch-Artefakte nicht nur erzeugt, sondern auch automatisiert gegen die
dokumentierte Drift-Grenze abgesichert werden.

## 6. Gebündeltes lokales Abschlussprofil

Für reguläre Arbeitspakete kann der verbindliche lokale Abschlussblock als
ein ausführbares Sammelprofil gestartet werden:

```bash
./tools/run_local_completion_checks.sh
```

Das Skript führt `compileall`, die Pytest-Suite, den CLI-Help-Smoke und – sofern
ein `chain_phase_telemetry_summary.txt` vorhanden ist – den
Ketten-Telemetrie-Drift-Gate-Check aus. Wenn ein Batchlauf zwingend ein Summary
erzeugen muss, wird die Drift-Artefaktprüfung mit `--require-drift-summary`
verbindlich gemacht:

```bash
./tools/run_local_completion_checks.sh --require-drift-summary
```

## 7. Automatisierter CI-Aufruf

Das lokale Abschlussprofil ist zusätzlich in GitHub Actions verdrahtet. Der
Workflow `.github/workflows/local-completion-checks.yml` startet auf Pull
Requests, Pushes auf die Hauptarbeitszweige und manuell per `workflow_dispatch`
denselben Sammelbefehl:

```bash
./tools/run_local_completion_checks.sh
```

Der Workflow enthält zusätzlich den Job `batch-artifact-drift-gate`. Dieser
legt ein repräsentatives `chain_phase_telemetry_summary.txt` mit
`drift_status=pass` an und startet dasselbe Abschlussprofil mit verpflichtender
Drift-Artefaktprüfung:

```bash
./tools/run_local_completion_checks.sh --require-drift-summary
```

## 8. Linux-Vendor-Kommando ausgeben

```bash
python -m src.imageCompositeConverter --print-linux-vendor-command --vendor-dir vendor
```

## 9. VS Code Debugging unter Windows

- Nutze nach Möglichkeit die Workspace-Launch-Konfiguration
  `ImageConverter: convert interactive range`.
- Falls `debugpy` in der geloggten `Command line` nur den Ordner
  `.venv\\Scripts` startet, ist der Interpreter falsch gewählt. In diesem Fall
  in VS Code explizit `.venv\\Scripts\\python.exe` auswählen.

## 10. Sample-Paar-Validierung (N5)

```bash
python -m tools.validate_sample_pairs --strict
python -m tools.validate_sample_pairs --render-missing-jpeg --report-csv artifacts/converted_images/reports/sample_pair_metrics.csv
```

Hinweis: `tools.validate_sample_pairs` lädt `fitz` (PyMuPDF) und `Pillow`
bei Bedarf automatisch auch aus den Repo-`vendor/*/site-packages`-Pfaden.
Wenn diese Pakete im `vendor`-Ordner liegen, ist kein zusätzlicher manueller
`pip install`-Schritt nötig.

## 11. N6-Variationssuite generieren (Basis)

```bash
python -m tools.generate_svg_variation_suite
```

Das Kommando erzeugt deterministische SVG-Szenarien für N6 in
`artifacts/images_to_convert/n6_variations` sowie einen Katalog in
`artifacts/converted_images/reports/n6_variation_catalog.csv`.
