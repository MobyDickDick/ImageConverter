def updateSuccessfulConversionsManifestWithMetrics(
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

    previous_manifest_metrics = _readSuccessfulConversionManifestMetrics(resolved_manifest_path)
    metrics_rows = collectSuccessfulConversionQualityMetrics(
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
        if _isSuccessfulConversionCandidateBetter(previous_metrics, row):
            accepted_metrics_by_variant[variant] = row
            effective_metrics_rows.append(row)
            accepted_improved_variants.add(variant)
            _storeSuccessfulConversionSnapshot(variant, row, svg_out_dir, reports_out_dir)
        else:
            if previous_metrics is not None:
                accepted_metrics_by_variant[variant] = previous_metrics
                effective_metrics_rows.append(_mergeSuccessfulConversionMetrics(row, previous_metrics))
            else:
                effective_metrics_rows.append(row)
            _restoreSuccessfulConversionSnapshot(variant, svg_out_dir, reports_out_dir)

    updated_lines: list[str] = []
    manifest_variants: set[str] = set()
    for raw_line in resolved_manifest_path.read_text(encoding='utf-8').splitlines():
        stripped = raw_line.split('#', 1)[0].strip()
        if not stripped:
            updated_lines.append(raw_line)
            continue
        variant = stripped.split(';', 1)[0].strip().upper()
        manifest_variants.add(variant)
        metrics = accepted_metrics_by_variant.get(variant)
        if metrics is None:
            updated_lines.append(raw_line)
            continue
        updated_lines.append(_formatSuccessfulConversionManifestLine(raw_line, metrics))

    missing_variants = [
        variant
        for variant in sorted(accepted_metrics_by_variant)
        if variant not in manifest_variants
    ]
    if missing_variants:
        if updated_lines and updated_lines[-1].strip():
            updated_lines.append('')
        for variant in missing_variants:
            updated_lines.append(
                _formatSuccessfulConversionManifestLine(
                    variant,
                    accepted_metrics_by_variant[variant],
                )
            )

    failed_entry = _latestFailedConversionManifestEntry(reports_out_dir)
    updated_without_failed = [
        line
        for line in updated_lines
        if "status=failed" not in line.lower()
    ]
    updated_lines = updated_without_failed
    if failed_entry is not None:
        failed_variant = str(failed_entry.get("variant", "")).strip().upper()
        failure_reason = str(failed_entry.get("failure_reason", "")).strip()
        if updated_lines and updated_lines[-1].strip():
            updated_lines.append("")
        failed_line = f"{failed_variant} ; status=failed"
        if failure_reason:
            failed_line += f" ; reason={failure_reason}"
        updated_lines.append(failed_line)

    resolved_manifest_path.write_text('\n'.join(updated_lines) + '\n', encoding='utf-8')
    return resolved_manifest_path, _sortedSuccessfulConversionMetricsRows(effective_metrics_rows)
