# Plan-B canvas expansion recheck, 2026-11-13

The user-provided `plan-b-workbench.zip` froze AC0022.svg with seed 472.
Its original and all 16 probes used a 35 × 112 pixel canvas. The scaled and
translated source viewport exceeded that canvas; probes 01, 09 and 15 failed.

The corrected Workbench expands the canvas symmetrically around the source
viewport before rasterization. Probe 01 now uses 39 × 124 pixels. All 17 cases
pass the real converter with the same source, seed, descriptions, transforms,
64 iterations, 60-second case timeout and unchanged quality limits.
The source/descriptions/transform correspondence is checked programmatically.

The recheck used two retained attempts: original and the three previous failures,
then the 13 remaining cases. Raw artifacts and audits remain locally under
`.tmp/plan-b-ac0022-expanded-seed472/`. The per-case before/after canvases,
metrics and source hash are recorded in `summary.json`.

Validation: 72 variation/Workbench tests pass, including enlarged renders as
independent clipping oracles, percent geometry, gradients, nonzero viewBox,
resource limits and preserving old reports during HTTP re-preparation. The
31 existing GUI tests also passed with the new preparation code (103 total).
Historical CLI acceptance replays retain their fixed-canvas defaults.
This verifies the reported example and canvas construction, not universal
conversion success for arbitrary motifs.
