# D5 Multi-Objective Prototype Evaluation (2026-04-12)

## Setup
- Weights: `pixel_error=1.00`, `geometry_penalty=0.35`, `semantic_penalty=1.00`.
- Objective: `pixel_error + geometry_penalty + semantic_penalty` with weights.
- `geometry_penalty` is normalized `mean_delta2` (`mean_delta2 / (median(mean_delta2)+1)`).
- `semantic_penalty` is `0` for `status=semantic_ok`, otherwise `1`.

## Family winners (A/B)
| Family | Baseline winner (`error_per_pixel`) | Prototype winner (weighted objective) |
| --- | --- | --- |
| AC0800 | AC0800_M | AC0800_M |
| AC0811 | AC0811_L | AC0811_L |
| AC0834 | AC0834_S | AC0834_S |
| AC0870 | AC0870_L | AC0870_L |
| AC0882 | AC0882_L | AC0882_L |

## Winner list (prototype rank improvements)
| Variant | Baseline rank | Prototype rank | Delta | Dominant reason |
| --- | ---: | ---: | ---: | --- |
| AC0800_S | 9 | 4 | -5 | lower normalized geometry penalty |
| AC0834_S | 10 | 8 | -2 | balanced objective |
| AC0800_M | 2 | 1 | -1 | lower normalized geometry penalty |
| AC0811_S | 6 | 5 | -1 | lower normalized geometry penalty |

## Error type observations
- Semantic mismatches in the evaluated slice: `0`.
- Geometry-driven rank increases: `4` variants.
- Geometry-driven rank decreases: `5` variants.
- No family winner changed; therefore no AC08 success-gate regression in this snapshot.

## Detailed rows
| Variant | status | error_per_pixel | mean_delta2 | geometry_penalty | prototype_score |
| --- | --- | ---: | ---: | ---: | ---: |
| AC0800_L | semantic_ok | 0.00769012 | 631.343 | 0.433 | 0.159357 |
| AC0800_M | semantic_ok | 0.00601250 | 53.910 | 0.037 | 0.018963 |
| AC0800_S | semantic_ok | 0.04594568 | 908.693 | 0.624 | 0.264240 |
| AC0811_L | semantic_ok | 0.00410153 | 541.832 | 0.372 | 0.134265 |
| AC0811_M | semantic_ok | 0.01306531 | 1455.943 | 0.999 | 0.362825 |
| AC0811_S | semantic_ok | 0.02479644 | 1066.456 | 0.732 | 0.280990 |
| AC0834_S | semantic_ok | 0.04832711 | 3926.960 | 2.695 | 0.991697 |
| AC0870_L | semantic_ok | 0.03176790 | 6839.047 | 4.694 | 1.674706 |
| AC0870_S | semantic_ok | 0.15126914 | 6616.800 | 4.542 | 1.740817 |
| AC0882_L | semantic_ok | 0.01167012 | 2773.643 | 1.904 | 0.677980 |
| AC0882_M | semantic_ok | 0.03499592 | 6716.563 | 4.610 | 1.648509 |
