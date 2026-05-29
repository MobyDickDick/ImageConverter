#!/usr/bin/env python3
"""Check a chain_phase_telemetry_summary.txt artifact as a drift gate."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.iCCModules import imageCompositeConverterBatchReporting as batch_reporting


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "summary_path",
        nargs="?",
        default="artifacts/converted_images/reports/chain_phase_telemetry_summary.txt",
        help="Path to chain_phase_telemetry_summary.txt (default: current reports artifact).",
    )
    args = parser.parse_args()

    result = batch_reporting.checkChainTelemetryDriftSummaryImpl(args.summary_path)
    reasons = ",".join(result.get("reasons", []))
    status = result.get("status", "missing")
    if result.get("accepted") is True:
        print(f"PASS chain telemetry drift gate: {args.summary_path}")
        return 0

    suffix = f" reasons={reasons}" if reasons else ""
    print(f"WARN chain telemetry drift gate: status={status}{suffix} path={args.summary_path}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
