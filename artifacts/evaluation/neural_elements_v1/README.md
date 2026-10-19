# Optional neural elements experiment

Three separately trained tiny CNNs; frozen real/synthetic inputs; 84 paired
production CLI attempts under identical five-second image deadlines.
Both arms accept 33/42 cases. No demonstrated real end-to-end benefit; the
analytic default is retained. All 377 archive pairs retain their hashes.

`summary.json`, `checks.json`, `manifest.json` and `models/` are compact evidence.
The complete report, raster copies, SVG outputs and raw telemetry are kept
locally in this directory and ignored by Git. CI uploads its own full evidence.
This summary does not replace independent verification of raw outputs.

Full protocol, observations, limitations and next work:
[NEURAL-ELEMENTS-01](../../../docs/next_arbeitspaket_2026-10-19_neural_elements.md).

Reproduce from a fresh checkout:

```powershell
.venv/Scripts/python.exe -m tools.run_neural_elements --output-dir .tmp/neural-study --work-dir .tmp/neural-study-work
.venv/Scripts/python.exe -m tools.run_neural_elements --verify-only --output-dir .tmp/neural-study
```

With the preserved local raw files, verification can instead target this folder.
