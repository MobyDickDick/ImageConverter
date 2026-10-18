# Production CLI anytime benchmark

The primary matrix compares the pre-scheduler Git snapshot `00d48fe5c` to
`90f8e7fee`: eight frozen cases, three seeds, four fixed image caps, two modes.
192 attempts produce 185 SVGs; 113 pass independent strict pixel and structure
checks. Failures remain in all success-rate denominators. Larger caps do not
solve the paraphrased Hz description, ellipse or triangle in either version.

`manifest.json` binds inputs and independent expectations. `report.json`
contains every outcome, per-split curves, paired comparisons, measured image
and batch times, source hashes and archive snapshots. `outputs/` retains all
saved SVGs, including rejected ones. `telemetry/` contains actual worker render
events and loaded module hashes. `checks.json` records the independent replay.

The primary before/60s/seed-42 batch has an unexplained 1311.579s interruption
outside its reported image times. It is retained. `diagnostic_replay/` is a
separate repeat taking 11.187s, with eight byte-identical outputs, excluded from
the primary summary. No general wall-time speedup is claimed.

Recheck from the repository root:

```powershell
.venv/Scripts/python.exe -m tools.run_anytime_benchmark --verify-only --output-dir artifacts/evaluation/anytime_search_v1
```

Protocol, full reproduction command and limitations:
`docs/next_arbeitspaket_2026-10-18_benchmark_anytime.md`.
