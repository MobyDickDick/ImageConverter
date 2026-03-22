# Open Tasks

This checklist only tracks work that is actionable for the ImageConverter in the
current repository snapshot. Older unrelated language/compiler/runtime tasks were removed so the list stays
focused on the actual project scope.

## How to use this list

- Work from top to bottom unless a dependency requires a different order.
- When a task is completed, change its checkbox to `- [x]` and add a short note.
- If a task splits into multiple deliverables, keep the parent item and add nested
  subtasks below it.

## Current status

- The latest committed AC08 report snapshot contains `54` evaluated AC08 validation logs, of which `43` are `semantic_ok` and `11` remain `semantic_mismatch`.
- The remaining failures are concentrated in the families `AC0800`, `AC0811`, `AC0813`, `AC0814`, `AC0831`, `AC0836`, and `AC0870`; the detailed breakdown now lives in `docs/ac08_artifact_analysis.md`.
- Continue to add new work items here before implementation starts, then mark them in-place when they are done.

## Next priority tasks

- [ ] Fix the vertical-connector semantic false positives in the remaining AC08 families.
  - Target `AC0811_M`, `AC0811_S`, `AC0813_L`, `AC0813_M`, `AC0831_M`, and `AC0836_L` first.
  - The current logs repeatedly report `Im Bild ist waagrechter Strich erkennbar, aber nicht in der Beschreibung enthalten`, although these families are expected to use vertical connectors or stems.
  - Extend primitive detection/reporting so each problematic run records whether the connector was classified as `vertical`, `horizontal`, or `ambiguous` before semantic validation fails.

- [ ] Harden circle detection for small AC08 variants before the semantic gate runs.
  - Prioritize `AC0811_S`, `AC0814_S`, and `AC0870_S`, where the reports also contain `Beschreibung erwartet Kreis, im Bild aber nicht robust erkennbar` and/or `Strukturprüfung: Kein belastbarer Kreis-Kandidat im Rohbild erkannt`.
  - Reuse the local mask / foreground fallback path already proven for thin-ring cases and expose enough instrumentation to tell whether the accepted circle came from Hough, foreground mask, or family-specific fallback.

- [x] Add a family-level semantic rule for the plain-ring family `AC0800`.
  - `AC0800` now derives `SEMANTIC: Kreis ohne Buchstabe` as an explicit semantic family instead of relying on text clues alone.
  - `AC0800_L`, `AC0800_M`, and `AC0800_S` are treated as currently optimal conversions and are locked into the AC08 regression suite so future adjustments must keep them `semantic_ok`.
  - `AC0800_S` now keeps the converted circle concentric with the template and may no longer shrink below the original template radius during circle-only validation, so the small plain-ring variant is no longer tracked as an open geometric follow-up.

- [ ] Refresh the AC08 reports after the next semantic round.
  - Re-run the affected AC08 families once the connector-orientation and circle-fallback fixes are in place.
  - Regenerate the committed report snapshot and update `docs/ac08_artifact_analysis.md` so the backlog reflects the new post-fix distribution instead of the current 43/11 split.

- [ ] Make the AC08 success gate actionable in the normal workflow.
  - Promote the metrics from `ac08_success_metrics.csv` / `ac08_success_criteria.txt` into a documented regression check so failed criteria are visible before the next backlog review.
  - Include validation-round instrumentation fixes if needed, because the current report still shows `mean_validation_rounds_per_file=0.000`, which is not yet decision-useful.

## Image conversion pipeline

- [x] Publish the detailed roadmap checklist referenced from the README.
  - Added this file so roadmap tasks can now be tracked and marked complete in-repo.

- [x] Improve error positions and messages.
  - Added a structured `DescriptionMappingError` with optional `SourceSpan` metadata so malformed CSV/XML description files now report exact file/line/column locations.
  - The CLI now surfaces these diagnostics as stable `[ERROR]` messages instead of failing with ambiguous parser exceptions.
  - Added regression tests for malformed XML, malformed CSV rows, and the CLI-facing error output.

## Tooling and documentation

- [x] Improve CLI wrapper ergonomics and documentation.
  - Added a proper CLI reference in `docs/image_converter_cli.md` with canonical convert/annotate/regression/vendor commands.
  - Updated the parser help text with examples, a clearer descriptions-table flag (`--descriptions-path` alias), a named `--iterations` override, and a default input directory for non-conversion helper flows.
  - Added regression tests that lock the new help text and the documented parser behaviors.

- [x] Stabilize formatter, lints, and local documentation workflows.
  - Added `docs/image_converter_workflow.md` as the canonical local verification sequence for compile/test/CLI-help checks.
  - Added regression tests that keep the workflow document referenced from the README and lock key command anchors.
  - Re-validated the documented tooling commands against the current parser/help surface.

## AC08 follow-up work

- [x] Continue improving AC08 output quality.
  - Added the generated reports `ac08_weak_family_status.csv` and `ac08_weak_family_status.txt`, which summarize remaining AC08 weak families from `pixel_delta2_ranking.csv` together with the currently implemented mitigation status and observed log markers.
  - Revalidated the new weak-family status reporting with targeted regression tests so the documentation task now has reproducible output instead of manual notes only.
  - Kept `docs/ac08_improvement_plan.md` aligned with the new reporting artifacts and the existing mitigation heuristics.

- [x] Document that the canonical open-task list is currently empty and keep roadmap references aligned.
  - Added an explicit current-status section here and synchronized the README/documentation index wording so future work is added back to the same checklist before implementation starts.

- [x] Materialize the AC08 weak-family follow-up reports referenced by the improvement plan.
  - Regenerated `artifacts/converted_images/reports/ac08_weak_family_status.csv` and `.txt` from the current `pixel_delta2_ranking.csv` so the documented AC08 follow-up now exists as committed snapshot artifacts, not only as code/tests.
