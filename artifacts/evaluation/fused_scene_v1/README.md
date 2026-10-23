# Native scene fusion: compact independent CLI evidence

Parent: `1f234c9c976cfd76a52448bf0c92a6bcdf80e993`.
Inputs are raster/description only. Conversion workers forbid reference SVG reads.
Every arm requests 64 iterations, search seed 17 and a supervised five-second
image budget without extension. Saved native outputs are independently rendered
and checked for pixels, object inventory, bounding boxes and painter order.

| Dataset | Parent | Fused runtime |
| --- | ---: | ---: |
| Frozen development, seed 20261020 | 0/12 | 12/12 |
| New rotated/paraphrased holdout, seed 862719 | 0/12 | 12/12 |
| Renamed holdout | — | 12/12, byte-identical |
| Independent Plan-B original + variations, seed 593187 | — | 17/17 |

Git retains only this README, the small aggregate `summary.json`, and
`checks.json` with test counts, source hashes and limitations. Generated PNGs,
SVGs, manifests and full per-case telemetry are ignored.

Full independently replayable evidence remains locally in
`.tmp/fusion-full-evidence/` and `.tmp/fusion-evidence-d73eb727c.zip`.
The original commit is recoverable from
`.tmp/fusion-before-slim-d73eb727c.bundle`. These local backups are not pushed.

To verify an existing full local evidence directory:

```powershell
.venv/Scripts/python.exe -m tools.summarize_fused_scene_evaluation --verify-only
```

A fresh clone contains no raw evidence. Generate fresh scenes and verify their
saved CLI outputs with the reproduction commands in the implementation document.
CI uploads its own full run as an artifact. Aggregate counts alone do not replace
independent raster/vector checks. No production code or quality limit changed
when shrinking this commit.

See [implementation and limits](../../../docs/history/next_arbeitspaket_2026-10-20_scene_fusion.md).
