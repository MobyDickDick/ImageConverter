def _format_successful_conversion_manifest_line(existing_line: str, metrics: dict[str, object]) -> str:
    """Render one enriched successful-conversions manifest line."""
    if not _successful_conversion_metrics_available(metrics):
        return existing_line.rstrip('\n')

    variant = str(metrics.get('variant', '')).strip().upper()
    prefix, comment = existing_line, ''
    if '#' in existing_line:
        prefix, comment = existing_line.split('#', 1)
        comment = '#' + comment.rstrip('\n').rstrip('\r').rstrip()
    prefix = prefix.strip()
    if not prefix:
        return existing_line.rstrip('\n')

    fields = [variant]
    status = str(metrics.get('status', '')).strip()
    if status:
        fields.append(f'status={status}')
    best_iteration = str(metrics.get('best_iteration', '')).strip()
    if best_iteration:
        fields.append(f'best_iteration={best_iteration}')
    for key, precision in (
        ('diff_score', 6),
        ('error_per_pixel', 8),
        ('total_delta2', 6),
        ('mean_delta2', 6),
        ('std_delta2', 6),
    ):
        value = float(metrics.get(key, float('nan')))
        if math.isfinite(value):
            fields.append(f'{key}={value:.{precision}f}')
    pixel_count = int(metrics.get('pixel_count', 0) or 0)
    if pixel_count > 0:
        fields.append(f'pixel_count={pixel_count}')

    line = ' ; '.join(fields)
    if comment:
        line += '  ' + comment
    return line
""" End move to File mainFiles/convert_rangeFiles/update_successful_conversions_manifest_with_metricsFiles/_format_successful_conversion_manifest_line.py """


""" Start move to File mainFiles/convert_rangeFiles/update_successful_conversions_manifest_with_metricsFiles/_latest_failed_conversion_manifest_entry.py
import src
"""
def _latest_failed_conversion_manifest_entry(reports_out_dir: str) -> dict[str, object] | None:
    """Return the most recent failed conversion as a manifest-like row."""
    summary_path = Path(reports_out_dir) / "batch_failure_summary.csv"
    if not summary_path.exists():
        return None

    latest_row: dict[str, str] | None = None
    try:
        with summary_path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f, delimiter=";")
            for row in reader:
                filename = str(row.get("filename", "")).strip()
                status = str(row.get("status", "")).strip().lower()
                if not filename or status not in {"render_failure", "batch_error", "semantic_mismatch"}:
                    continue
                latest_row = row
    except OSError:
        return None

    if latest_row is None:
        return None

    variant = Path(str(latest_row.get("filename", "")).strip()).stem.upper()
    if not variant:
        return None

    return {
        "variant": variant,
        "status": "failed",
        "failure_reason": str(latest_row.get("reason", "")).strip(),
    }
""" End move to File mainFiles/convert_rangeFiles/update_successful_conversions_manifest_with_metricsFiles/_latest_failed_conversion_manifest_entry.py """


""" Start move to File mainFiles/convert_rangeFiles/update_successful_conversions_manifest_with_metrics.py
import src
"""
