def _write_successful_conversion_csv_table(csv_path: str | os.PathLike[str], metrics: list[dict[str, object]]) -> str:
    """Write the successful-conversions leaderboard as a CSV table."""
    csv_path = os.fspath(csv_path)
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    with open(csv_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow([
            'variant', 'status', 'image_found', 'svg_found', 'log_found', 'best_iteration',
            'diff_score', 'error_per_pixel', 'pixel_count', 'total_delta2', 'mean_delta2', 'std_delta2',
        ])
        for row in _sorted_successful_conversion_metrics_rows(metrics):
            writer.writerow([
                row['variant'],
                row['status'],
                int(bool(row['image_found'])),
                int(bool(row['svg_found'])),
                int(bool(row['log_found'])),
                row['best_iteration'],
                '' if not math.isfinite(float(row['diff_score'])) else f"{float(row['diff_score']):.6f}",
                '' if not math.isfinite(float(row['error_per_pixel'])) else f"{float(row['error_per_pixel']):.8f}",
                int(row['pixel_count']),
                '' if not math.isfinite(float(row['total_delta2'])) else f"{float(row['total_delta2']):.6f}",
                '' if not math.isfinite(float(row['mean_delta2'])) else f"{float(row['mean_delta2']):.6f}",
                '' if not math.isfinite(float(row['std_delta2'])) else f"{float(row['std_delta2']):.6f}",
            ])
    return csv_path


def write_successful_conversion_quality_report(
    folder_path: str,
    svg_out_dir: str,
    reports_out_dir: str,
    successful_variants: list[str] | tuple[str, ...] | None = None,
    output_name: str = 'successful_conversion_quality',
) -> tuple[str, str, list[dict[str, object]]]:
    """Backward-compatible wrapper that now also refreshes the manifest."""
    manifest_path, metrics = update_successful_conversions_manifest_with_metrics(
        folder_path=folder_path,
        svg_out_dir=svg_out_dir,
        reports_out_dir=reports_out_dir,
        successful_variants=successful_variants,
    )

    sorted_metrics = _sorted_successful_conversion_metrics_rows(metrics)
    csv_path = _write_successful_conversion_csv_table(
        os.path.join(reports_out_dir, f'{output_name}.csv'),
        sorted_metrics,
    )
    leaderboard_csv_path = _write_successful_conversion_csv_table(
        os.path.join(reports_out_dir, 'successful_conversions.csv'),
        sorted_metrics,
    )
    txt_path = os.path.join(reports_out_dir, f'{output_name}.txt')

    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(f'manifest_path={manifest_path}\n')
        f.write(f'leaderboard_csv_path={leaderboard_csv_path}\n')
        f.write(f'variants_updated={len(sorted_metrics)}\n')
    return csv_path, txt_path, sorted_metrics


