# Rectangular gradient parents in the common structure search

Synthetic development under SEARCH-STRUCTURE-01, starting at `b5781dd76`.
Twelve unchanged CLI inputs improve from **0/12 to 12/12**; another seed passes
**12/12**, and one coupled Plan-B cohort passes **17/17**. Every final conversion
uses `primitive_mixed_gradient_scene_v1`, a supervised five-second image budget,
seed 17, 64 requested iterations and the unchanged native/object/region/pixel gates.

The parent kind is explicit in the fully consumed contract. Four visible sharp
corners and straight sides seed the rectangular gradient boundary. A bright rim
requires independent color evidence and measured coverage. The resulting native
parent reuses the same flat child proposals, bounded instance/island agenda,
observed depth ordering, group/singleton topology and registration as the circle
parent. Extra residual regions retain their own local pixel checks. The existing
eight-child and 96-state bounds remain in force. Child rounding is explicitly
scoped; rounded or cropped rectangular parents remain unsupported.

`summary.json` records paired input/reference/description/annotation hashes,
output hashes, independent native/local/global measurements, budget controls,
selected sources and runtime fingerprints. Final CLI source snapshots match the
current runtime. `checks.json` records commands, exit codes, JUnit hashes and the
initial failed development tests as well as the corrected final checks. Raw CLI
trees, references and JUnit files remain local in `.tmp/rectangular-parent/`.

The focused scene/evidence regression passes **972/972 tests**, including
**54 new controls**, with exit 0 and no skips. It also covers the existing circle
path, separate rectangular scene path, rounded/outlining/overlap operators,
structure agenda and reserve integrity. Its 1,200-second outer guard is retained;
the suite completes in 745 seconds. The separate core profile passes **42/42**.
Syntax, whitespace, package links and historical freeze integrity checks pass.

The frozen HC0010 and Rail families remain **sealed_unrun**, with zero converter
trials and `accepted=null`. Historical integrity is checked without requiring
later runtime development to match the frozen source snapshot. No catalogue,
reserve file or archived conversion is changed. This is not independent real
family acceptance, a full standard-suite run or an archive reconversion.
SEARCH-STRUCTURE-01, GENERAL-SCENE-COMPOSITION-09 and GENERAL-SCENE-REAL-05 stay open.

Use fresh destinations for replay:

```powershell
.venv/Scripts/python.exe -m tools.evaluate_rectangular_parent --prepare .tmp/rect-parent-inputs-new --seed 716293
.venv/Scripts/python.exe -m tools.evaluate_rectangular_parent --inputs .tmp/rect-parent-inputs-new --output .tmp/rect-parent-cli-new --require-all
.venv/Scripts/python.exe -m tools.evaluate_rectangular_parent --inputs .tmp/rect-parent-inputs-new --output .tmp/rect-parent-cli-new --verify-only --require-all
.venv/Scripts/python.exe -m tools.evaluate_rectangular_parent --prepare .tmp/rect-parent-variants-new --seed 853197 --variations
.venv/Scripts/python.exe -m tools.evaluate_rectangular_parent --inputs .tmp/rect-parent-variants-new --output .tmp/rect-parent-variants-cli-new --require-all
.venv/Scripts/python.exe -m pytest tests/test_rectangular_gradient_parent.py tests/test_mixed_topology.py tests/test_gradient_scene_runtime.py -q
```

For the paired baseline, prepare with the new independent generator and run the
same inputs against `b5781dd76` without `--require-all`. The CI job
`rectangular-gradient-parent` runs the new controls and the second CLI seed.

See the [German work package and remaining scope](../../../docs/next_arbeitspaket_2026-11-05_rectangular_parent.md).
