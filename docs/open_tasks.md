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

- The canonical task list now contains follow-up work for the remaining AC08 quality gaps from the latest committed reports.
- Continue to add new work items here before implementation starts, then mark them in-place when they are done.

## Next priority tasks

- [x] Eliminate the remaining AC08 batch/render failures for `AC0811_L` and `AC0812_M`.
  - Revalidated the previously missing anchor cases on 2026-03-21 with targeted `convert_range(..., start_ref="AC0811", end_ref="AC0811")` and `convert_range(..., start_ref="AC0812", end_ref="AC0812")` runs: `AC0811_L.svg` and `AC0812_M.svg` are emitted again and their element-validation logs now report `status=semantic_ok`.
  - Added a regression test that locks those two historical failure cases so future changes do not silently fall back to `*_failed.svg`.
  - The committed AC08 summary artifacts still describe the older snapshot and should be regenerated in a dedicated follow-up once the broader AC08 report set is refreshed.

- [ ] Reduce the worst residual deltas for the still-weak AC08 families.
  - Prioritize `AC0820_L`, `AC0835_S`, `AC0882_S`, `AC0837_L`, `AC0831_L`, `AC0839_S`, and `AC0834_S` from `ac08_weak_family_status.txt`.
  - Focus on family-specific quality improvements that preserve the new no-regression guardrails, especially for `_S` variants and stubborn connector geometries.

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
