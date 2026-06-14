# Changelog
- The complete core test suite was revalidated with 765 passing tests, and its full pytest output is now versioned as a GitHub review artifact.

## 2026-06-01
- AC0100_L/M/S now use renderer-stable algorithmic gradient bands in the non-composite elementwise symbol fit, dropping the local QA metric from roughly 53k mean_delta2 to below 4k without selecting fixed sample SVGs or template transfer.
- GitHub Actions now runs the satisfactory regression battery as a separate heavy job, reconverting all stored successful baseline variants and failing on worse mean_delta2 quality.

All notable changes to ImageConverter will be documented in this file.

## Unreleased

- T6.7 Run PQ restores the real quarantined `AC0811_L` fixture to the focused long-bottom-stem geometry test, limits the conversion to one complete iteration, and explicitly rejects validation-budget timeouts, reducing its isolated runtime from the historical `102.33s` to `2.80s`.

- T6.6 Run PP keeps the real `AC0835_S` semantic regression coverage while limiting this focused case to one complete element-validation round, reducing its isolated runtime from the historical `133.60s` to `43.25s`.

- Plan-B Run PH adds a description-driven connector-free circle/text badge Geometry-IR for `AC0845_S`, reducing `normalized_mse` from `0.04927739` to `0.03350944` and completing the currently qualified rotation.

- Plan-B Run PG extends general Geometry-IR registration to rectangle bodies, reducing `AC0722_1_S` from `normalized_mse=0.05681223` to `0.01399280` with the shared left-rotated square-kelle topology and rotating the queue to `AC0845_S`.

- Plan-B Run PF adds a description-driven, size-relative Geometry-IR for the upright AC0701 square-kelle, reducing `AC0701_1_S` from `normalized_mse=0.05935915` to `0.00287122` and rotating the queue to `AC0722_1_S` and `AC0845_S`.

- Plan-B Run PE confirms the shared right-facing AC0732 square-kelle Geometry-IR on `AC0732_1_S`, reducing `normalized_mse` from `0.06000391` to `0.01875864` and rotating the queue to the three remaining qualified candidates.

- Plan-B Run PD adds a description-driven circular-damper Geometry-IR for `AC0254_2`, correcting the former rectangle assumption, reducing `normalized_mse` from `0.06059016` to `0.00300936`, and rotating the queue to `AC0732_1_S` through `AC0845_S`.

- Plan-B Run PC verifies the shared right-facing AC0732 square-kelle Geometry-IR on `AC0732_1_L`, reducing `normalized_mse` from `0.06552955` to `0.03083937` and rotating the queue to `AC0254_2` through `AC0845_S`.

- Plan-B Run PB adds a typo-tolerant, description-driven Geometry-IR for the right-facing AC0732 square-kelle with a horizontal P glyph, reducing `AC0732_1_M` from `normalized_mse=0.06993533` to `0.01700694` and rotating the queue to `AC0732_1_L` through `AC0722_1_S`.

- The AC0010/AC0100 family regression now covers the unsuffixed `AC0010` base image together with `AC0100_L/M/S`, enforcing algorithmic Geometry-IR or raster-fit output, per-path quality limits, and the absence of sample/template fallback for every real family member.

- Plan-B Run PA adds a description-driven Geometry-IR for the vertically mirrored AC0723 square-kelle symbol while keeping its T glyph horizontal, reducing `AC0723_1_S` from `normalized_mse=0.07402805` to `0.01126597` and rotating the queue to `AC0732_1_M` through `AC0701_1_S`.

- Plan-B Run OZ adds a description-driven Geometry-IR for the left-rotated AC0722 square-kelle symbol while keeping its T glyph horizontal, reducing `AC0722_1_L` from `normalized_mse=0.07686921` to `0.02420340` and rotating the queue to `AC0723_1_S` through `AC0732_1_S`.

- Plan-B Run OY confirms the right-rotated AC0733 square-kelle Geometry-IR on `AC0733_1_M`, reducing `normalized_mse` from `0.08842208` to `0.01822546` without variant-specific geometry and rotating the queue to `AC0722_1_L` through `AC0254_2`.

- Plan-B Run OX adds a description-driven Geometry-IR for the right-rotated AC0733 square-kelle symbol while keeping its P glyph horizontal, reducing `AC0733_1_L` from `normalized_mse=0.09223704` to `0.01388032` and rotating the queue to `AC0733_1_M` through `AC0732_1_L`.

- Plan-B Run OW confirms that the description-driven, raster-fitted AC0551 chevron topology generalizes to `AC0551_2_M`, reducing `normalized_mse` from `0.09445446` to `0.01688702` and rotating the queue to `AC0733_1_L` through `AC0732_1_M`.

- Plan-B Run OV validates the description-driven pump Geometry-IR on `AC0253_1`, reducing `normalized_mse` from `0.10473690` to `0.01705962` and rotating the queue to `AC0551_2_M` through `AC0723_1_S`.

- Plan-B Run OU makes saturated dark-light-dark gradient estimation robust against bright frames and chevrons, reducing `AC0150_2` from `normalized_mse=0.10493784` to `0.04095022` and rotating the queue to `AC0253_1` through `AC0722_1_L`.

- Plan-B Run OT adds a description-driven pump Geometry-IR with a circle and rotation-aware triangle, reducing `AC0403_1_M` from `normalized_mse=0.11117438` to `0.02203193` and rotating the queue to `AC0150_2` through `AC0733_1_M`.

- Plan-B Run OS adds a description-driven, raster-fitted right-chevron primitive to the non-composite symbol fit, reducing `AC0551_1_M` from `normalized_mse=0.14916385` to `0.02316318` and rotating the queue to `AC0403_1_M` through `AC0733_1_L`.

- Plan-B Run OR applies description-declared quarter turns to diagonal topology, reducing `AC0502_1_M` from `normalized_mse=0.15533278` to `0.01602799` and rotating the queue to `AC0551_1_M` through `AC0551_2_M`.

- Plan-B Run OQ generalizes the non-composite symbol fit for description-declared diagonals, center dots, raster-derived RGB gradients, and shortened diagonal extents; `AC0531_1_S` drops from `normalized_mse=0.15610678` to `0.02479964` and rotates out in favor of `AC0253_1`.

- Plan-B Run OP re-converts `AC0820_L` through the description-driven semantic CO₂ badge path, replaces the stale connector-only SVG, lowers `normalized_mse` from `0.05117826` to `0.03823352`, and rotates PF8/triage to `AC0531_1_S` through `AC0150_2`.

- Plan-B Run OM refreshes all quality evidence and synchronizes a new five-item rotation led by `AC0820_L`; PF8 classifies four perception questions as generalized and the `AC0551_1_M` rectangle/rule case as special-case only.

- Plan-B Run OL schließt die Run-OG-Rotation mit einem dimensionstreuen AC0130-Kühlelement aus Metallverlauf, Außenrechteck, beschnittenem Andreaskreuz und zwei Minuszeichen ab; `normalized_mse` sinkt auf `0.00985252` und PF8/Triage sind synchron leer.

- Plan-B Run OK rekonstruiert `AC0130_M` als dimensionstreuen Metallverlauf mit sichtbaren vertikalen Partitionen, senkt `normalized_mse` auf `0.00153867` und rotiert den Kandidaten aus PF8/Triage.

- AC0414_S now uses a topology-preserving partitioned-circle SVG, reducing normalized MSE from 0.31829609 to 0.00360827 while rotating Plan-B/PF8 to AC0130_M.

- AC0922_S now has a corrected quality baseline (`normalized_mse=0.02747206`); a rectangle-shaped re-conversion regression is rejected while the accepted circle/left-connector snapshot is regression-tested and Plan-B/PF8 rotates to AC0414_S.

- AC0835_L was re-converted as a connector-free semantic VOC badge, reducing normalized MSE from 0.05726039 to 0.03911266 and rotating Plan-B/PF8 to AC0922_S.

- AC0863_S completed its real Plan-B/PF8 acceptance run as a semantic rF badge with an upper connector (`status=semantic_ok`, `mean_delta2=4155.215820`); active perception targets now rotate strictly to AC0864_S.

- FP-Recovery Run OD makes isolated one-file refinement measurable without weakening multi-file quality selection; the full gate now passes with 14/14 reports, 6/6 preserved anchors, 3 accepted improvements, and 0 accepted regressions.

- FP-Recovery Run OC now confirms 14/14 AC08 iteration reports and all 6 Previously-Good anchors at the regular 32-iteration budget; release remains blocked because isolated one-file segments produce no measurable quality-pass improvement.

- The segmented AC08 runner now resolves quarantined variant source folders and requires the expected `Iteration_Log.csv` row before marking a segment complete; aggregation independently rejects stale markers without matching report data.

- FP-D14 now records the final data-based decision as **not yet complete**: only 10/14 variants have iteration records, 3/6 Previously-Good anchors are retained, no quality improvement is measured, and release remains blocked until the documented recovery thresholds are met.

- The FP-D13 release gate now propagates named evidence paths into segmented AC08 runs and can aggregate an empty optional quality-pass report without fabricating improvements; the quantitative gate remains red when the baseline criteria are not met.

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

### Plan-B AC0864_S Run OF (2026-06-06)

- `AC0864` als semantisches AC08-`rF`-Badge mit horizontal gespiegelter Rechtsarm-Geometrie ergänzt; der reale 25x15-Ein-Datei-Lauf endet mit `status=semantic_ok`, `best_error=17.986667` und `mean_delta2=3699.607910`.
- Den letzten aktiven PF8-Kandidaten nach generalisiertem Kreis-/Linien-Lerneffekt entfernt; Kandidatenliste und Linkage-Report sind nun synchron leer und warten auf eine neue Qualitätsauswertung.
