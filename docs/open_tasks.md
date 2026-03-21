# Open Tasks

This file is the detailed checklist referenced from the README roadmap.
It turns the roadmap bullets into explicit, trackable tasks so the next item can
be taken from documentation and marked complete when finished.

## How to use this list

- Work from top to bottom unless a dependency requires a different order.
- If a roadmap item refers to code that is not part of the current repository snapshot, archive it with a short rationale instead of leaving it perpetually open.
- When a task is completed, change its checkbox to `- [x]` and add a short note.
- If a task splits into multiple deliverables, keep the parent item and add nested
  subtasks below it.

## Frontend / language

- [x] Publish the detailed roadmap checklist referenced from the README.
  - Added this file so roadmap tasks can now be tracked and marked complete in-repo.

- [x] Improve error positions and messages.
  - Added a structured `DescriptionMappingError` with optional `SourceSpan` metadata so malformed CSV/XML description files now report exact file/line/column locations.
  - The CLI now surfaces these diagnostics as stable `[ERROR]` messages instead of failing with ambiguous parser exceptions.
  - Added regression tests for malformed XML, malformed CSV rows, and the CLI-facing error output.
- [x] Refine the linter.
  - Archived for the current ImageConverter repository snapshot: the TinyLanguage linter sources and their regression suite are not present here, so this roadmap item cannot be executed in-repo as originally written.
  - Documented the repository-scope mismatch in the README/open-task guidance so future work picks the next actionable item instead of blocking on a non-existent subsystem.

## Type discipline

- [x] Remove implicit type changes.
  - Archived for the current ImageConverter repository snapshot: the TinyLanguage type-checking/interpreter sources that would define coercion behavior across expressions, functions, and heap operations are not present in this checkout.
  - Documented the repository-scope mismatch here so roadmap work continues with the next actionable in-repo task instead of blocking on a missing subsystem.
- [x] Evaluate simple type inference.
  - Archived for the current ImageConverter repository snapshot: the repository only contains the image-conversion pipeline plus its tests/docs, not the TinyLanguage parser/type-checker sources where a separate inference pass would exist.
  - Decision: no in-repo implementation is justified here because there is no maintainable host subsystem for inference logic in this checkout; future work should revisit the idea only in a repository snapshot that again contains the TinyLanguage type-analysis pipeline.

## Runtime

- [ ] Harden the heap API.
  - Improve invalid-pointer diagnostics.
  - Report out-of-bounds access details more precisely.
  - Detect double-delete scenarios.
  - Add simple leak tracking for development workflows.
- [ ] Expand runtime regression coverage.
  - Add nested-array scenarios.
  - Add many `new/delete` pair stress cases.
  - Add deep-recursion coverage.
  - Add explicit heap-failure scenarios.

## Tooling

- [x] Improve CLI wrapper ergonomics and documentation.
  - Added a proper CLI reference in `docs/image_converter_cli.md` with canonical convert/annotate/regression/vendor commands.
  - Updated the parser help text with examples, a clearer descriptions-table flag (`--descriptions-path` alias), a named `--iterations` override, and a default input directory for non-conversion helper flows.
  - Added regression tests that lock the new help text and the documented parser behaviors.
- [ ] Stabilize formatter, lints, and language-server workflows.
  - Document the expected local workflow.
  - Add or refresh regression checks for formatter/lint behavior.
  - Verify the language-server path used in documentation remains current.

## Native backends

- [ ] Keep the C backend stable and documented.
  - Re-run smoke tests when backend behavior changes.
  - Keep `docs/c_backend.md` aligned with the current limitations and workflow.
- [ ] Continue LLVM emission experiments as a separate track.
  - Keep experimental work isolated from the stable path.
  - Document scope, limitations, and exit criteria for the experiment.
