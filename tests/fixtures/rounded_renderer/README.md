Frozen librsvg controls for SVG-ROUNDED-RENDERER-01 (2026-11-07).

The SVGs and reference PNGs were saved **before** changing the production
renderer, using `tools.evaluate_rounded_renderer --prepare`. `manifest.json`
records the librsvg version, SVG/PNG hashes, crop boxes and native radii.
The 24 rounded cases include six repeated controls; 18 have distinct SVGs.
Four additional controls cover sharp rectangles, circles, ellipses and paths.
Tests read these exact PNGs without requiring librsvg or regenerating pixels.

`before_png_sha256` records the old MuPDF renders retained locally in
`.tmp/rounded-renderer/controls/*-before.png`. Those old-renderer PNGs are
diagnostic artifacts, not the test references. The compact before/after results
are retained in `artifacts/evaluation/rounded_renderer_v1/summary.json`.

`historical_same_paint.png` and its JSON retain the exact negative MuPDF input
from the 2026-10-24 seed 372851 (`probe_04`), checked against its original
manifest hash. The test keeps its old pixels. Correct rim paint measurement
now lets these original pixels pass all native and raster gates too; freshly
rendering the same SVG is checked separately. Zero or one unoccluded corner
must still be rejected in a direct independent-pixel observation test.
