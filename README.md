# ImageConverter

ImageConverter converts badge/source images into composite SVG outputs and also
provides annotation/debugging helpers for the source raster files.

## Main entry point

Run the converter via:

```bash
python -m src.image_composite_converter
```

The detailed CLI reference lives in [docs/image_converter_cli.md](docs/image_converter_cli.md).
The recommended local verification workflow lives in
[docs/image_converter_workflow.md](docs/image_converter_workflow.md).

## Repository layout

- `src/image_composite_converter.py` — converter implementation and CLI.
- `tests/test_image_composite_converter.py` — regression tests for the converter.
- `docs/image_converter_cli.md` — command reference.
- `docs/image_converter_workflow.md` — local verification workflow.
- `docs/ac08_improvement_plan.md` — AC08 improvement backlog/history.
- `docs/ac08_artifact_analysis.md` — AC08 artifact analysis notes.
- `docs/open_tasks.md` — current ImageConverter task list.

## Quick start

### Convert images into SVG outputs

```bash
python -m src.image_composite_converter \
  artifacts/images_to_convert \
  --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml \
  --output-dir artifacts/converted_images \
  --start AC0000 \
  --end ZZ9999
```

### Qualitätsparameter für als gut markierte Konvertierungen

```bash
python -m src.successful_conversion_quality_app
```

Die kleine Anwendung liest `artifacts/converted_images/reports/successful_conversions.txt`, ergänzt die dort bereits als erfolgreich markierten Varianten automatisch um Qualitätskennzahlen wie `total_delta2 = Σ((ΔR)^2 + (ΔG)^2 + (ΔB)^2)`, `mean_delta2` und `std_delta2` und schreibt zusätzlich weiterhin einen CSV/TXT-Report zur Übersicht.

### Annotate source images

```bash
python -m src.image_composite_converter \
  --mode annotate \
  --output-dir artifacts/annotated_images \
  --start AC0811 \
  --end AC0814
```

## Tests and checks

```bash
python -m compileall src tests
python -m pytest
python -m src.image_composite_converter --help
python -m src.image_composite_converter artifacts/images_to_convert --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --ac08-regression-set --output-dir artifacts/converted_images
# neue erfolgreich konvertierte Bild-IDs in artifacts/converted_images/reports/successful_conversions.txt eintragen; Qualitätswerte werden danach automatisch an diese Einträge ergänzt
```

## VS Code / Windows troubleshooting

Wenn VS Code beim Starten mit `debugpy` einen Fehler wie `Couldn't spawn debuggee: [WinError 5] Zugriff verweigert` meldet und in der geloggten `Command line` nur der Ordner `...\.venv\Scripts` statt `...\.venv\Scripts\python.exe` auftaucht, ist meist der Python-Interpreter falsch ausgewählt.

- Wähle in VS Code über `Python: Select Interpreter` explizit die Datei `.venv\Scripts\python.exe` aus — **nicht** den Ordner `.venv\Scripts`.
- Verwende bevorzugt die mitgelieferte Debug-Konfiguration `ImageConverter: convert interactive range`; sie startet den Einstiegspunkt als Modul (`python -m src.image_composite_converter`) und setzt das Workspace-Verzeichnis korrekt.
- Falls du lieber direkt im Terminal prüfst, funktioniert derselbe Start auch ohne Debugger mit `python -m src.image_composite_converter artifacts/images_to_convert --interactive-range`.
