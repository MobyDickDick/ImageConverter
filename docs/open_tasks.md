# Open Tasks

This file is the detailed checklist referenced from the README roadmap.
It turns the roadmap bullets into explicit, trackable tasks so the next item can
be taken from documentation and marked complete when finished.

## How to use this list

- Work from top to bottom unless a dependency requires a different order.
- When a task is completed, change its checkbox to `- [x]` and add a short note.
- If a task splits into multiple deliverables, keep the parent item and add nested
  subtasks below it.

## Frontend / language

- [x] Publish the detailed roadmap checklist referenced from the README.
  - Added this file so roadmap tasks can now be tracked and marked complete in-repo.

- [ ] Improve error positions and messages.
  - Carry line/column information consistently through tokens.
  - Preserve location metadata on AST nodes where diagnostics originate.
  - Unify diagnostics behind an error type that can optionally expose a `SourceSpan`.
  - Add regression tests for parser and runtime-facing error messages.
- [ ] Refine the linter.
  - Add "must-use" tracking across control-flow branches.
  - Emit unreachable-code warnings in common dead-code scenarios.
  - Lock behavior with focused regression tests.

## Type discipline

- [ ] Remove implicit type changes.
  - Define uniform coercion rules across expressions, functions, and heap operations.
  - Reject implicit type changes where semantics are ambiguous.
  - Document the resulting rules and edge cases.
- [ ] Evaluate simple type inference.
  - Decide whether a minimal inference pass is worth the maintenance cost.
  - If yes, document the supported scope and limitations before implementation.

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

- [ ] Improve CLI wrapper ergonomics and documentation.
  - Review wrapper command surface for consistency.
  - Ensure help text and docs use the canonical commands.
  - Add/update smoke tests for the documented CLI flows.
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
