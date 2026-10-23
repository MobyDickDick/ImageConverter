# Frozen real transfer evidence

Two actual supervised CLI trials on unchanged runtime `8b4b2f18f`: **0/2
accepted**. GENERAL-SCENE-REAL-05 remains open. These are now exposed data
for future development. Historical catalogue exposure and lack of an
independent human annotation audit limit independence claims.

`freeze.json` fixes annotations, runtime hashes and protocol before conversion.
`inputs/` retains neutral decoded inputs; `originals/` retains JPEGs. `trial/`
retains rejected SVGs, comparisons, CLI result rows, access guards and timing.
`manifest.json` seals the inventory. Raw commands refer to original execution
paths; verification uses retained files relative to here.

```powershell
.venv/Scripts/python.exe -m tools.verify_real_scene_transfer_evidence artifacts/evaluation/real_scene_transfer_v1/manifest.json --output .tmp/transfer-verified.json
```

Exit 0 verifies consistent evidence without rerunning the converter. Add
`--require-all` to demand positive acceptance: this experiment must return 1.
See [scope, causes and next development](../../../docs/history/next_arbeitspaket_2026-10-22_real_scene_transfer.md).
