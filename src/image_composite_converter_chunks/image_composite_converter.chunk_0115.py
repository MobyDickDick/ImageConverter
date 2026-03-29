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


def update_successful_conversions_manifest_with_metrics(
    folder_path: str,
    svg_out_dir: str,
    reports_out_dir: str,
    manifest_path: Path | None = None,
    successful_variants: list[str] | tuple[str, ...] | None = None,
) -> tuple[Path, list[dict[str, object]]]:
    """Update ``successful_conversions.txt`` as an in-place best list.

    New conversion data is only accepted when it improves the persisted quality
    metrics. Regressions are rejected, and whenever a previous best snapshot is
    available the converter output/log for that variant is restored so the
    working output stays aligned with the manifest.
    """
    resolved_manifest_path = Path(manifest_path) if manifest_path is not None else Path(reports_out_dir) / 'successful_conversions.txt'
    if not resolved_manifest_path.exists():
        raise FileNotFoundError(f'Successful-conversions manifest not found: {resolved_manifest_path}')

    previous_manifest_metrics = _read_successful_conversion_manifest_metrics(resolved_manifest_path)
    metrics_rows = collect_successful_conversion_quality_metrics(
        folder_path=folder_path,
        svg_out_dir=svg_out_dir,
        reports_out_dir=reports_out_dir,
        successful_variants=successful_variants or _load_successful_conversions(resolved_manifest_path),
    )

    accepted_metrics_by_variant: dict[str, dict[str, object]] = {}
    effective_metrics_rows: list[dict[str, object]] = []
    accepted_improved_variants: set[str] = set()
    for row in metrics_rows:
        variant = str(row['variant']).upper()
        previous_metrics = previous_manifest_metrics.get(variant)
        if _is_successful_conversion_candidate_better(previous_metrics, row):
            accepted_metrics_by_variant[variant] = row
            effective_metrics_rows.append(row)
            accepted_improved_variants.add(variant)
            _store_successful_conversion_snapshot(variant, row, svg_out_dir, reports_out_dir)
        else:
            if previous_metrics is not None:
                accepted_metrics_by_variant[variant] = previous_metrics
                effective_metrics_rows.append(_merge_successful_conversion_metrics(row, previous_metrics))
            else:
                effective_metrics_rows.append(row)
            _restore_successful_conversion_snapshot(variant, svg_out_dir, reports_out_dir)

    updated_lines: list[str] = []
    manifest_variants: set[str] = set()
    for raw_line in resolved_manifest_path.read_text(encoding='utf-8').splitlines():
        stripped = raw_line.split('#', 1)[0].strip()
        if not stripped:
