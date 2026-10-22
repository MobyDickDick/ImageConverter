# Mixed gradient scene evidence

Two original JPEGs, unchanged descriptions and frozen visible object marks.
The initial independent-of-runtime real transfer failed 0/2. The originals
were then used for development; the final code passes 2/2 and the renamed
repeat is byte-identical. This is development evidence, not acceptance of
two untouched real families. GENERAL-SCENE-REAL-05 remains open.

`manifest.json` binds original pixels and saved SVGs for baseline, first
transfer and subsequent development. `initial-annotations.json` preserves
the original marks; the current config correctly labels these as development.
`first-freeze.json` and `final-freeze.json` bind the runtime source snapshots.
`acceptance.json` contains independently re-rendered native-object, region,
strict pixel and regular satisfaction checks. `trial-summary.json` retains
diagnostic and timeout attempts in their denominators. Full raw attempts
are local under `.tmp/concept-audit/` and require regeneration elsewhere.

`concept-probes.json` retains the semantic roundtrip counterexample and
archive-path/ID checks. `checks.json` records the final validation commands.
The archive retains 379 pairs; this package does not change that count.

Recheck the retained original/vector evidence:

```powershell
.venv/Scripts/python.exe -m tools.verify_mixed_gradient_scene_evidence artifacts/evaluation/mixed_gradient_scene_v1/manifest.json --output .tmp/mixed-evidence-check.json
```
