# Image Converter CLI

This document is the canonical command reference for the repository's runnable CLI:
`python -m src.image_composite_converter`.

## Recommended commands

### Convert a range into SVG outputs

```bash
python -m src.image_composite_converter \
  artifacts/images_to_convert \
  --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml \
  --output-dir artifacts/converted_images \
  --start AC0000 \
  --end ZZ9999
```

- `artifacts/images_to_convert` is the default input folder, so it can be omitted in
  local workflows when that directory is used.
- `--descriptions-path` is the preferred descriptive name for the legacy
  `--csv-path` option. Both flags are accepted and resolve to the same parser field.

### Run the fixed AC08 regression set

```bash
python -m src.image_composite_converter \
  --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml \
  --output-dir artifacts/converted_images \
  --ac08-regression-set
```

This forces the documented AC08 symbol subset and expands the effective range to the
 full `AC0000..ZZ9999` scan while passing the fixed regression variant allowlist
 into the conversion pipeline.

### Annotate source images instead of converting them

```bash
python -m src.image_composite_converter \
  --mode annotate \
  --output-dir artifacts/annotated_images \
  --start AC0811 \
  --end AC0814
```

In this mode the tool writes marked-up raster outputs plus coordinate sidecars
instead of conversion artifacts.

### Print the Linux vendor install command

```bash
python -m src.image_composite_converter \
  --print-linux-vendor-command \
  --vendor-dir vendor \
  --vendor-platform manylinux2014_x86_64 \
  --vendor-python-version 311
```

This command does not require an explicit input directory anymore; it only prints the
`pip` invocation needed to vendor Linux wheels for optional image dependencies.

## Positional compatibility mode

The CLI still accepts the historical positional form:

```bash
python -m src.image_composite_converter INPUT_DIR TABLE_OR_OUTPUT 128
```

- If the second positional argument ends in `.csv`, `.tsv`, or `.xml`, it is treated
  as the descriptions table path.
- Otherwise it is treated as the output directory.
- If no explicit descriptions table is given, the CLI auto-detects a nearby
  CSV/TSV/XML file and prefers obvious mapping/export filenames.

## Range handling

- `--start` and `--end` skip the interactive console prompt.
- If both are missing, the CLI asks for `Namen von` / `Namen bis`.
- `--interactive-range` forces the prompt even when defaults are available.
- When both prompt entries are partial tokens rather than full references, the tool
  falls back to substring filtering.

## Iterations

The converter supports both forms:

```bash
python -m src.image_composite_converter INPUT_DIR OUTPUT_DIR 64
python -m src.image_composite_converter INPUT_DIR OUTPUT_DIR --iterations 64
```

The named option is preferred for scripts because it keeps commands self-describing.
