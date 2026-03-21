# Open Tasks

This checklist only tracks work that is actionable for the ImageConverter in the
current repository snapshot. Historical TinyLanguage/compiler/runtime tasks were
removed so the list stays focused on the actual project scope.

## How to use this list

- Work from top to bottom unless a dependency requires a different order.
- When a task is completed, change its checkbox to `- [x]` and add a short note.
- If a task splits into multiple deliverables, keep the parent item and add nested
  subtasks below it.

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

- [ ] Stabilize formatter, lints, and local documentation workflows.
  - Document the expected local workflow for image-converter changes.
  - Add or refresh regression checks for formatter/lint behavior.
  - Verify the documented tooling commands remain current.

## AC08 follow-up work

- [ ] Continue improving AC08 output quality.
  - Re-run the fixed regression set after relevant pipeline changes.
  - Document remaining weak symbol families and their current mitigation status.
  - Keep `docs/ac08_improvement_plan.md` aligned with the implemented heuristics and reports.
