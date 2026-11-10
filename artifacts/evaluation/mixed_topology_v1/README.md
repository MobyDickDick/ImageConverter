# Mixed overlap groups and isolated forms

Synthetic development only, under SEARCH-STRUCTURE-01. Twelve frozen CLI
inputs improve from **0/12 to 12/12**; another seed passes **12/12**, and one
coupled Plan-B cohort passes **17/17**. All final conversions use the shared
`primitive_mixed_gradient_scene_v1` path, a supervised five-second budget,
seed 17 and unchanged native/object/region/pixel gates.

The complete contract binds the number of overlapping connected components
and isolated objects. All separate components must retain clear native rims.
Ordering uses observed paint/rims, and negative evidence includes both counts.
The existing eight-child and 96-state limits remain in force.

`summary.json` records input/description/annotation/output hashes, measured
quality, independent native checks and runtime snapshots. `checks.json`
records commands, exit codes and report hashes. Raw CLI trees and JUnit files
remain local under `.tmp/mixed-topology/`; replay from the generator to create
fresh evidence. The original comparison inputs did not change when explicit
SVG gradient defaults were added to make references self-checkable: all
twelve decoded raster hashes, descriptions and object annotations are equal.

All **658 scene regressions** pass, including **59 new tests**. The combined
713-test development run had one failure: the old test required the current
runtime to remain identical to the historical freeze. After adjusting only
that test module, all **55 evidence tests** pass in a separate run; the
production runtime is identical between runs. The separate core profile
passes **42/42**. The original nonzero combined exit and the final evidence
rerun are both retained in `checks.json`; this is not a claimed green combined
713-test run. Syntax, diff and historical freeze integrity checks also pass.

The reserved HC0010 and Rail families remain **sealed_unrun**, with zero
converter trials and `accepted=null`. Historical integrity is verified without
requiring subsequent runtime development to match the frozen source snapshot.
Explicit current-runtime comparison still rejects source drift. No reserve
files, catalogues or archived conversions were changed.

No positive independent real-family transfer, full standard-suite acceptance
or archive reconversion is claimed. SEARCH-STRUCTURE-01,
GENERAL-SCENE-COMPOSITION-09 and GENERAL-SCENE-REAL-05 remain open.

Replay with fresh destinations:

```powershell
.venv/Scripts/python.exe -m tools.evaluate_mixed_topology --prepare .tmp/topology-inputs-new --seed 641927
.venv/Scripts/python.exe -m tools.evaluate_mixed_topology --inputs .tmp/topology-inputs-new --output .tmp/topology-cli-new --require-all
.venv/Scripts/python.exe -m tools.evaluate_mixed_topology --inputs .tmp/topology-inputs-new --output .tmp/topology-cli-new --verify-only --require-all
.venv/Scripts/python.exe -m tools.evaluate_mixed_topology --prepare .tmp/topology-variants-new --seed 853197 --variations
.venv/Scripts/python.exe -m tools.evaluate_mixed_topology --inputs .tmp/topology-variants-new --output .tmp/topology-variants-cli-new --require-all
.venv/Scripts/python.exe -m pytest tests/test_mixed_topology.py tests/test_overlap_groups.py tests/test_real_composition_holdout_freeze.py -q
```

The starting implementation is commit `88d062c00`. To repeat the paired
baseline, prepare inputs with the new independent generator, then run them
in that source checkout without `--require-all`; all failures remain in the
denominator. The CI job `disconnected-overlap-groups` replays the additional
seed and includes the new positive and negative controls.

See [German work package and remaining scope](../../../docs/next_arbeitspaket_2026-11-04_mixed_topology.md).
