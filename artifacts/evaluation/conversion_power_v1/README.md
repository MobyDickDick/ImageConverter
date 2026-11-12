# Conversion power request evidence, 2026-11-11

Scope: API lifetime and controlled interruption handling. No actual machine
sleep, battery-duration or new catalog quality acceptance was attempted.

| Check | Result |
| --- | --- |
| Power/timing/deadline/catalog regression | 54 passed, exit 0, no skips |
| Separate core-green profile | 42 passed, exit 0, no skips |
| Native Windows API probe outside sandbox | Passed, exit 0 |
| Open handles, normal completion | 153 → 154 → 153 |
| Open handles, controlled cancellation | 153 → 154 → 153 |

The native observation is retained in [native_probe.json](native_probe.json).
Commands, JUnit counts and implementation/evidence hashes are retained in
[checks.json](checks.json).
The first sandboxed probe returned Windows error 5 (access denied); the
conversion reports this as `unavailable`. The outside-sandbox probe confirms
the real API can acquire both SYSTEM and EXECUTION and release its handle.
Neither observation proves that all Windows policies honor the request during
actual standby. Display requests and power-plan modifications are absent.

Reproduce from the repository root with Python 3.10 and requirements-dev:

```powershell
.venv/Scripts/python.exe -m pytest -q tests/test_conversion_power.py tests/test_conversion_timing.py tests/test_conversion_deadline.py tests/test_run_catalog_conversion.py --junitxml=.tmp/power-request-regression.xml
.venv/Scripts/python.exe tools/run_pytest_profile.py core-green --junitxml=.tmp/power-request-core.xml
.venv/Scripts/python.exe -m tools.check_conversion_power --report .tmp/conversion-power-native.json
git diff --check
```

The probe intentionally returns nonzero on Windows if requests are unavailable
or handle cleanup fails. On other platforms it checks the explicit unsupported
path. Local JUnit files remain under `.tmp/`; the CI job uploads fresh reports.
The new CI job has not been run on GitHub in this session.

The interruption regression pauses the observer for over five seconds, keeps
the original one-second budget, rejects a late handoff and verifies worker
termination. The report distinguishes the observation gap from observer CPU
time and records an undetermined cause; it never treats these seconds as
confirmed active worker computation. Existing checked-output recovery and
catalog continuation/resume regressions remain passing.
