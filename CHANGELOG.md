# Changelog
## 2026-06-01
- AC0100_L/M/S now use renderer-stable algorithmic gradient bands in the non-composite elementwise symbol fit, dropping the local QA metric from roughly 53k mean_delta2 to below 4k without selecting fixed sample SVGs or template transfer.
- GitHub Actions now runs the satisfactory regression battery as a separate heavy job, reconverting all stored successful baseline variants and failing on worse mean_delta2 quality.

All notable changes to ImageConverter will be documented in this file.

## Unreleased

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
