"""Reporting helper for successful conversion quality artifacts."""

from __future__ import annotations

import os


def writeSuccessfulConversionQualityReportImpl(
    *,
    folder_path: str,
    svg_out_dir: str,
    reports_out_dir: str,
    update_manifest_fn,
    sort_rows_fn,
    write_csv_fn,
    successful_variants: list[str] | tuple[str, ...] | None = None,
    output_name: str = "successful_conversion_quality",
) -> tuple[str, str, list[dict[str, object]]]:
    """Backward-compatible report writer that refreshes the quality manifest."""
    manifest_path, metrics = update_manifest_fn(
        folder_path=folder_path,
        svg_out_dir=svg_out_dir,
        reports_out_dir=reports_out_dir,
        successful_variants=successful_variants,
    )

    sorted_metrics = sort_rows_fn(metrics)
    csv_path = write_csv_fn(
        os.path.join(reports_out_dir, f"{output_name}.csv"),
        sorted_metrics,
    )
    leaderboard_csv_path = write_csv_fn(
        os.path.join(reports_out_dir, "successful_conversions.csv"),
        sorted_metrics,
    )
    txt_path = os.path.join(reports_out_dir, f"{output_name}.txt")

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(f"manifest_path={manifest_path}\n")
        f.write(f"leaderboard_csv_path={leaderboard_csv_path}\n")
        f.write(f"variants_updated={len(sorted_metrics)}\n")

    return csv_path, txt_path, sorted_metrics
