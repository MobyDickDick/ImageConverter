# Image Converter Local Workflow

This document defines the repository's expected local verification flow for
ImageConverter changes. The commands below are intentionally limited to tools
that are already used inside this repository snapshot so the workflow stays
stable across environments.

## Baseline verification sequence

Run these commands from the repository root before submitting ImageConverter
changes:

```bash
python -m compileall src tests
python -m pytest
python -m src.image_composite_converter --help
```

- `python -m compileall src tests` is the lightweight syntax/formatting guard for
  the current repo state. It quickly catches malformed edits in both the runtime
  module and the regression tests.
- `python -m pytest` is the canonical regression suite.
- `python -m src.image_composite_converter --help` is the CLI documentation smoke
  test: the help output must continue to advertise the current user-facing
  commands and option names.

## When CLI or docs change

If a change touches parser flags, examples, or documented workflows, re-run the
baseline commands and then verify the affected command variants directly:

```bash
python -m src.image_composite_converter \
  artifacts/images_to_convert \
  --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml \
  --output-dir artifacts/converted_images \
  --ac08-regression-set

python -m src.image_composite_converter \
  --print-linux-vendor-command \
  --vendor-dir vendor \
  --vendor-platform manylinux2014_x86_64 \
  --vendor-python-version 311
```

Use the first command when conversion-path changes could affect the documented
AC08 workflow. Use the second command when dependency/bootstrap instructions or
vendor guidance changed.

## Documentation update rule

Keep this file, `docs/image_converter_cli.md`, and the roadmap entries in
`README.md` / `docs/open_tasks.md` aligned whenever the local workflow changes.
The tests keep a small set of command anchors in sync, but maintainers should
still review the prose examples after parser updates.
