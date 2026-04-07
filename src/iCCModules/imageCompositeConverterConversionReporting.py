"""Post-conversion reporting helpers for convertRange."""

from __future__ import annotations


def runPostConversionReportingImpl(
    *,
    folder_path: str,
    csv_path: str,
    iterations: int,
    svg_out_dir: str,
    diff_out_dir: str,
    reports_out_dir: str,
    normalized_selected_variants: set[str],
    result_map: dict[str, dict[str, object]],
    write_semantic_audit_report_fn,
    write_pixel_delta2_ranking_fn,
    write_ac08_weak_family_status_report_fn,
    write_ac08_regression_manifest_fn,
    write_ac08_success_criteria_report_fn,
    emit_ac08_success_gate_status_fn,
    successful_conversions_manifest,
    update_successful_conversions_manifest_fn,
    generate_conversion_overviews_fn,
    print_fn=print,
) -> dict[str, str]:
    """Execute final report writing/manifest refresh for one convertRange run."""
    write_semantic_audit_report_fn(
        reports_out_dir,
        [
            dict(audit)
            for row in result_map.values()
            for audit in [dict(row.get("params", {}).get("semantic_audit", {}))]
            if audit
        ],
    )
    write_pixel_delta2_ranking_fn(folder_path, svg_out_dir, reports_out_dir)
    sorted_selected_variants = sorted(normalized_selected_variants)
    write_ac08_weak_family_status_report_fn(
        reports_out_dir,
        selected_variants=sorted_selected_variants,
    )
    write_ac08_regression_manifest_fn(
        reports_out_dir,
        folder_path=folder_path,
        csv_path=csv_path,
        iterations=iterations,
        selected_variants=sorted_selected_variants,
    )
    ac08_success_gate = write_ac08_success_criteria_report_fn(
        reports_out_dir,
        selected_variants=sorted_selected_variants,
    )
    emit_ac08_success_gate_status_fn(ac08_success_gate)
    if successful_conversions_manifest.exists():
        update_successful_conversions_manifest_fn(
            folder_path=folder_path,
            svg_out_dir=svg_out_dir,
            reports_out_dir=reports_out_dir,
            manifest_path=successful_conversions_manifest,
        )
    generated_overviews = generate_conversion_overviews_fn(diff_out_dir, svg_out_dir, reports_out_dir)
    if generated_overviews:
        print_fn(
            "[INFO] Übersichts-Kacheln erzeugt: "
            + ", ".join(f"{key}={path}" for key, path in sorted(generated_overviews.items()))
        )
    return generated_overviews
