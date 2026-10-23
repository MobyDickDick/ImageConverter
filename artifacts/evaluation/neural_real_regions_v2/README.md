# Real-region optional CNN experiment

NEURAL-ELEMENTS-REAL-02 freezes 27 original rasters and 63 visually annotated
regions before training/augmentation: nine training families, six development
families from the previous experiment, and ten new holdout families.
Three fixed training seeds are crossed with three search seeds in paired,
budget-controlled production CLI attempts. No demonstrated end-to-end benefit
justifies changing the analytic default.

`manifest.json`, `region_audit.json`, `summary.json`, `checks.json` and `models/`
are compact versioned evidence. Original copies, full predictions, SVGs and
raw worker telemetry remain local and are uploaded as CI artifacts.
A clean checkout regenerates a run before verification; compact summaries
alone do not replace independently rerendering outputs.

Protocol, limitations, results and next work:
[NEURAL-ELEMENTS-REAL-02](../../../docs/history/next_arbeitspaket_2026-10-19_neural_real_regions.md).

```powershell
.venv/Scripts/python.exe -m tools.run_real_neural_elements --output-dir .tmp/neural-real-study --work-dir .tmp/neural-real-work
.venv/Scripts/python.exe -m tools.run_real_neural_elements --verify-only --output-dir .tmp/neural-real-study
```
