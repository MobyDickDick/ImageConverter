#!/usr/bin/env python3
"""Validate the AC08 success metrics CSV emitted by a release-candidate smoke run."""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

REQUIRED_CRITERIA: tuple[str, ...] = (
    "criterion_no_new_batch_aborts",
    "criterion_no_accepted_regressions",
    "criterion_validation_rounds_recorded",
    "criterion_regression_set_improved",
    "criterion_stable_families_not_worse",
    "overall_success",
)


def _read_metrics(path: Path) -> dict[str, str]:
    metrics: dict[str, str] = {}
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle, delimiter=";")
        for row in reader:
            if len(row) < 2:
                continue
            name = row[0].strip()
            value = row[1].strip()
            if name and name.lower() != "metric":
                metrics[name] = value
    return metrics


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "metrics_path",
        nargs="?",
        default="artifacts/converted_images/reports/ac08_success_metrics.csv",
        help="Path to ac08_success_metrics.csv (default: current converted-images report).",
    )
    args = parser.parse_args()

    metrics_path = Path(args.metrics_path)
    if not metrics_path.exists():
        print(f"FAIL AC08 quality gate: missing metrics file: {metrics_path}", file=sys.stderr)
        return 1

    metrics = _read_metrics(metrics_path)
    missing = [name for name in REQUIRED_CRITERIA if name not in metrics]
    failed = [name for name in REQUIRED_CRITERIA if metrics.get(name) not in {"1", "1.0", "true", "True"}]
    if missing or failed:
        if missing:
            print("FAIL AC08 quality gate: missing criteria: " + ", ".join(missing), file=sys.stderr)
        if failed:
            print(
                "FAIL AC08 quality gate: failed criteria: "
                + ", ".join(f"{name}={metrics.get(name, '<missing>')}" for name in failed),
                file=sys.stderr,
            )
        print(f"Metrics: {metrics_path}", file=sys.stderr)
        return 1

    mean_rounds = metrics.get("mean_validation_rounds_per_file", "n/a")
    print(f"PASS AC08 quality gate: {metrics_path} (mean_validation_rounds_per_file={mean_rounds})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
