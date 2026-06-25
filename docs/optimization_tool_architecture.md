# Optimization Tool Architecture

## Goal

The converter keeps image loading, SVG rendering and raster comparison in the
image/rendering layer, while scalar search logic is exposed as a reusable
optimization tool. The tool contract is intentionally small:

```text
parameter variables + error function + algorithm/budget
        -> best parameter set + best error + stop reason
```

## API contract

The initial v1 interface lives in
`src/iCCModules/imageCompositeConverterOptimizationTool.py`:

- `OptimizationVariable`: name, inclusive lower/upper bounds and optional current
  value.
- `OptimizationProblem`: one or more variables, an error function accepting a
  parameter dictionary, optional maximum evaluations and improvement epsilon.
- `evaluateCandidateGridImpl(...)`: finite-grid optimizer that clips candidates
  to bounds, evaluates the supplied error function and reports the best finite
  candidate.
- `OptimizationResult`: best parameters, best error, evaluation count,
  convergence flag and stop reason.

The optimization tool does not import OpenCV, SVG rendering helpers or converter
state. Those concerns stay behind the caller-provided error function.

## Current integration

The existing element-width bracketing path now delegates candidate selection to
`evaluateCandidateGridImpl(...)`. The image part still builds candidate widths,
renders candidates and computes element error, but the choice of the best
parameter is made through the generic optimization tool seam.

```text
image part
  ├─ derive element-specific width bounds
  ├─ render/evaluate candidate via error_fn
  └─ call optimization tool
        └─ return best width + error/stop metadata
```

## Extension path

Future optimizers can share the same contract by replacing the finite-grid
algorithm with stochastic, coordinate-descent or multi-variable algorithms while
keeping the same `OptimizationProblem`/`OptimizationResult` boundary.
