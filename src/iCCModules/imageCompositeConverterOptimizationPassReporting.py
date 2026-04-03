"""Quality-pass reporting helpers extracted from the converter monolith."""

from __future__ import annotations

import csv
import os


def writeQualityPassReportImpl(
    reports_out_dir: str,
    pass_rows: list[dict[str, object]],
) -> None:
    if not pass_rows:
        return

    out_path = os.path.join(reports_out_dir, "quality_tercile_passes.csv")
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow([
            "pass",
            "filename",
            "old_error_per_pixel",
            "new_error_per_pixel",
            "old_mean_delta2",
            "new_mean_delta2",
            "improved",
            "decision",
            "iteration_budget",
            "badge_validation_rounds",
        ])
        for row in pass_rows:
            writer.writerow([
                row["pass"],
                row["filename"],
                f"{float(row['old_error_per_pixel']):.8f}",
                f"{float(row['new_error_per_pixel']):.8f}",
                f"{float(row.get('old_mean_delta2', float('inf'))):.6f}",
                f"{float(row.get('new_mean_delta2', float('inf'))):.6f}",
                "1" if bool(row["improved"]) else "0",
                row.get("decision", "accepted_improvement" if bool(row["improved"]) else "rejected_regression"),
                row["iteration_budget"],
                row["badge_validation_rounds"],
            ])


def evaluateQualityPassCandidateImpl(
    old_row: dict[str, object],
    new_row: dict[str, object],
) -> tuple[bool, str, float, float, float, float]:
    """Return whether a quality-pass candidate should replace the previous result."""

    prev_error_pp = float(old_row.get("error_per_pixel", float("inf")))
    new_error_pp = float(new_row.get("error_per_pixel", float("inf")))
    prev_mean_delta2 = float(old_row.get("mean_delta2", float("inf")))
    new_mean_delta2 = float(new_row.get("mean_delta2", float("inf")))
    error_improved = new_error_pp + 1e-9 < prev_error_pp
    delta2_improved = new_mean_delta2 + 1e-6 < prev_mean_delta2
    improved = error_improved or delta2_improved
    decision = "accepted_improvement" if improved else "rejected_regression"
    return improved, decision, prev_error_pp, new_error_pp, prev_mean_delta2, new_mean_delta2
