"""Finalization helpers for convertRange post-processing."""

from __future__ import annotations

import os

def runConversionFinalizationImpl(
    *,
    reports_out_dir: str,
    quality_logs: list[dict[str, object]],
    conversion_bestlist_path,
    conversion_bestlist_rows: dict[str, dict[str, object]],
    batch_failures: list[dict[str, str]],
    strategy_logs: list[dict[str, object]],
    files: list[str],
    result_map: dict[str, dict[str, object]],
    folder_path: str,
    csv_path: str,
    iterations: int,
    svg_out_dir: str,
    diff_out_dir: str,
    normalized_selected_variants: set[str],
    write_quality_pass_report_fn,
    write_conversion_bestlist_metrics_fn,
    write_batch_failure_summary_fn,
    write_strategy_switch_template_transfers_report_fn,
    write_iteration_log_and_collect_semantic_results_fn,
    harmonize_semantic_size_variants_fn,
    run_post_conversion_reporting_fn,
) -> list[dict[str, object]]:
    """Write run artifacts and trigger semantic harmonization/reporting."""
    write_quality_pass_report_fn(reports_out_dir, quality_logs)
    write_conversion_bestlist_metrics_fn(conversion_bestlist_path, conversion_bestlist_rows)
    write_batch_failure_summary_fn(reports_out_dir, batch_failures)
    if strategy_logs:
        write_strategy_switch_template_transfers_report_fn(reports_out_dir, strategy_logs)

    log_path = os.path.join(reports_out_dir, "Iteration_Log.csv")
    semantic_results = write_iteration_log_and_collect_semantic_results_fn(files, result_map, log_path)

    harmonize_semantic_size_variants_fn(semantic_results, folder_path, svg_out_dir, reports_out_dir)
    run_post_conversion_reporting_fn(
        folder_path=folder_path,
        csv_path=csv_path,
        iterations=iterations,
        svg_out_dir=svg_out_dir,
        diff_out_dir=diff_out_dir,
        reports_out_dir=reports_out_dir,
        normalized_selected_variants=normalized_selected_variants,
        result_map=result_map,
    )
    return semantic_results
