"""Batch/reporting helper functions extracted from imageCompositeConverter."""

from __future__ import annotations

import csv
import os


def readValidationLogDetailsImpl(log_path: str) -> dict[str, str]:
    if not os.path.exists(log_path):
        return {}
    details: dict[str, str] = {}
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line or ": " in line.split("=", 1)[0]:
                    continue
                if "=" not in line:
                    continue
                key, value = line.split("=", 1)
                details[key] = value
    except OSError:
        return {}
    return details


def writeBatchFailureSummaryImpl(reports_out_dir: str, failures: list[dict[str, str]]) -> None:
    summary_path = os.path.join(reports_out_dir, "batch_failure_summary.csv")
    with open(summary_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["filename", "status", "reason", "details", "log_file"])
        for failure in failures:
            writer.writerow(
                [
                    failure.get("filename", ""),
                    failure.get("status", ""),
                    failure.get("reason", ""),
                    failure.get("details", ""),
                    failure.get("log_file", ""),
                ]
            )
