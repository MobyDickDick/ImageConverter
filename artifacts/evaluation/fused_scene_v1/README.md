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

`manifest.json` retains frozen raster hashes and independent object oracles.
`summary.json` retains all decisions, runtime observations and source hashes.
`checks.json` records regression and archive checks with their limitations.
The shared compact schema is `layered_scene_*_v1`; it supports both containment
and partial-overlap painter-order constraints. These are synthetic capabilities,
not an overall catalog success rate. No quality limits were relaxed.

```powershell
.venv/Scripts/python.exe -m tools.summarize_fused_scene_evaluation --verify-only
```

Raw reproducible runs remain under `.tmp/fusion-*`; CI retains its own full run.
See [implementation and limits](../../../docs/next_arbeitspaket_2026-10-20_scene_fusion.md).
