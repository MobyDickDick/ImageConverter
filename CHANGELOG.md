# Changelog

All notable changes to ImageConverter will be documented in this file.

## Unreleased

- AC0232_S now uses a description-driven, left-rotated top-kelle Geometry-IR glyph with an `M` label before the generic non-composite fallback.
- AC0203_1 now uses a description-driven Geometry-IR path with a red circle and main-diagonal mirrored compressor line primitives before the generic non-composite symbol fallback.
- AC0150_L now uses a description-driven Geometry-IR path with vertical rectangle, horizontal rule-set, and right-side orthogonal polyline primitives before the generic non-composite symbol fallback.
- CI now includes a separate batch-artifact drift-gate job that runs the local completion profile with `--require-drift-summary` against a representative passing telemetry summary.
- Repository scope cleaned up so only ImageConverter-related source, tests, and documentation remain.
- Revalidated the former AC08 anchor failures `AC0811_L` and `AC0812_M`, added a regression test that requires real SVG output for both cases, and updated the open-task list to reflect that the code path is fixed while the committed AC08 reports still need refresh.
- Semantic validation now treats robust local circle masks as valid fallback evidence for vertical connector badges, so `AC0811_M` no longer gets rejected just because raw Hough circle detection misses the ring while the stem remains correct. `AC0811_L` stays explicitly tracked as a good conversion anchor.
