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
```
