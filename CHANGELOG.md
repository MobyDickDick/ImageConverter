# Changelog
## 2026-06-01
- AC0100_L/M/S now use renderer-stable algorithmic gradient bands in the non-composite elementwise symbol fit, dropping the local QA metric from roughly 53k mean_delta2 to below 4k without selecting fixed sample SVGs or template transfer.
- GitHub Actions now runs the satisfactory regression battery as a separate heavy job, reconverting all stored successful baseline variants and failing on worse mean_delta2 quality.

All notable changes to ImageConverter will be documented in this file.

## Unreleased

- The release-candidate AC08 smoke now runs each fixed regression variant in an isolated timeout segment and publishes aggregate success metrics only after all 14 segments complete.

- AC0862_S now uses the semantic AC08 rF left-connector badge path, giving the Plan-B candidate a real SVG output with a 3853.575928 mean_delta2 one-iteration probe and rotating the queue to AC0863_S/AC0864_S.
- AC0861_S now uses the semantic AC08 rF lower-stem connector badge path, with PF8 rotation updated to AC0862_S/AC0863_S/AC0864_S.
- AC0850_M now uses the semantic AC08 rF circle/text badge path instead of failing conversion, including rF text-scale tuning and Plan-B rotation to the next rF connector probe.
- AC0838_M was revalidated in the Plan-B/Perception rotation and removed from the active candidate list after the isolated VOC badge run fell below the review threshold.
- AC0232_S now uses a description-driven, left-rotated top-kelle Geometry-IR glyph with an `M` label before the generic non-composite fallback.
- AC0203_1 now uses a description-driven Geometry-IR path with a red circle and main-diagonal mirrored compressor line primitives before the generic non-composite symbol fallback.
- AC0150_L now uses a description-driven Geometry-IR path with vertical rectangle, horizontal rule-set, and right-side orthogonal polyline primitives before the generic non-composite symbol fallback.
- CI now includes a separate batch-artifact drift-gate job that runs the local completion profile with `--require-drift-summary` against a representative passing telemetry summary.
- Repository scope cleaned up so only ImageConverter-related source, tests, and documentation remain.
- Revalidated the former AC08 anchor failures `AC0811_L` and `AC0812_M`, added a regression test that requires real SVG output for both cases, and updated the open-task list to reflect that the code path is fixed while the committed AC08 reports still need refresh.
- Semantic validation now treats robust local circle masks as valid fallback evidence for vertical connector badges, so `AC0811_M` no longer gets rejected just because raw Hough circle detection misses the ring while the stem remains correct. `AC0811_L` stays explicitly tracked as a good conversion anchor.
- AC0870_S now exposes path-based T glyph position/scale to the shared optimizer, reducing the small T-badge mean delta from 6616.799805 to 5075.666504 and rotating the Plan-B queue to AC0850_M/AC0836_S/AC0844_S.
