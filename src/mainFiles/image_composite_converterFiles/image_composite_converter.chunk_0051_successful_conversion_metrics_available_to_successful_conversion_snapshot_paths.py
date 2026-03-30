def _successful_conversion_metrics_available(metrics: dict[str, object]) -> bool:
    """Return whether a metrics row contains fresh conversion data worth persisting."""
    status = str(metrics.get('status', '')).strip()
    if status:
        return True

    best_iteration = str(metrics.get('best_iteration', '')).strip()
    if best_iteration:
        return True

    pixel_count = int(metrics.get('pixel_count', 0) or 0)
    if pixel_count > 0:
        return True

    for key in ('diff_score', 'error_per_pixel', 'total_delta2', 'mean_delta2', 'std_delta2'):
        value = float(metrics.get(key, float('nan')))
        if math.isfinite(value):
            return True
    return False
""" End move to File mainFiles/convert_rangeFiles/update_successful_conversions_manifest_with_metricsFiles/_format_successful_conversion_manifest_lineFiles/_successful_conversion_metrics_available.py """


""" Start move to File mainFiles/convert_rangeFiles/update_successful_conversions_manifest_with_metricsFiles/_read_successful_conversion_manifest_metricsFiles/_parse_successful_conversion_manifest_line.py
import src
"""
def _parse_successful_conversion_manifest_line(raw_line: str) -> tuple[str, dict[str, object]]:
    """Parse one successful-conversions manifest line into variant plus metrics."""
    stripped = raw_line.split('#', 1)[0].strip()
    if not stripped:
        return '', {}

    parts = [part.strip() for part in stripped.split(';') if part.strip()]
    if not parts:
        return '', {}

    variant = parts[0].upper()
    metrics: dict[str, object] = {'variant': variant}
    for field in parts[1:]:
        if '=' not in field:
            continue
        key, value = [token.strip() for token in field.split('=', 1)]
        if not key:
            continue
        if key == 'pixel_count':
            with contextlib.suppress(ValueError):
                metrics[key] = int(value)
            continue
        if key in {'diff_score', 'error_per_pixel', 'total_delta2', 'mean_delta2', 'std_delta2'}:
            with contextlib.suppress(ValueError):
                metrics[key] = float(value.replace(',', '.'))
            continue
        metrics[key] = value
    return variant, metrics
""" End move to File mainFiles/convert_rangeFiles/update_successful_conversions_manifest_with_metricsFiles/_read_successful_conversion_manifest_metricsFiles/_parse_successful_conversion_manifest_line.py """


""" Start move to File mainFiles/convert_rangeFiles/update_successful_conversions_manifest_with_metricsFiles/_read_successful_conversion_manifest_metrics.py
import src
"""
def _read_successful_conversion_manifest_metrics(manifest_path: Path) -> dict[str, dict[str, object]]:
    """Load persisted best-list metrics keyed by variant."""
    if not manifest_path.exists():
        return {}

    rows: dict[str, dict[str, object]] = {}
    for raw_line in manifest_path.read_text(encoding='utf-8').splitlines():
        variant, metrics = _parse_successful_conversion_manifest_line(raw_line)
        if variant:
            rows[variant] = metrics
    return rows
""" End move to File mainFiles/convert_rangeFiles/update_successful_conversions_manifest_with_metricsFiles/_read_successful_conversion_manifest_metrics.py """


""" Start move to File mainFiles/convert_rangeFiles/update_successful_conversions_manifest_with_metricsFiles/_restore_successful_conversion_snapshotFiles/_successful_conversion_snapshot_pathsFiles/_successful_conversion_snapshot_dir.py
import src
"""
def _successful_conversion_snapshot_dir(reports_out_dir: str) -> Path:
    """Directory used to persist best-of artifacts for successful conversions."""
    return Path(reports_out_dir) / 'successful_conversions_bestlist'
""" End move to File mainFiles/convert_rangeFiles/update_successful_conversions_manifest_with_metricsFiles/_restore_successful_conversion_snapshotFiles/_successful_conversion_snapshot_pathsFiles/_successful_conversion_snapshot_dir.py """


""" Start move to File mainFiles/convert_rangeFiles/update_successful_conversions_manifest_with_metricsFiles/_restore_successful_conversion_snapshotFiles/_successful_conversion_snapshot_paths.py
import src
"""
def _successful_conversion_snapshot_paths(reports_out_dir: str, variant: str) -> dict[str, Path]:
    base_dir = _successful_conversion_snapshot_dir(reports_out_dir)
    base_dir.mkdir(parents=True, exist_ok=True)
    return {
        'svg': base_dir / f'{variant}.svg',
        'log': base_dir / f'{variant}_element_validation.log',
        'metrics': base_dir / f'{variant}.json',
    }
""" End move to File mainFiles/convert_rangeFiles/update_successful_conversions_manifest_with_metricsFiles/_restore_successful_conversion_snapshotFiles/_successful_conversion_snapshot_paths.py """


""" Start move to File mainFiles/convert_rangeFiles/update_successful_conversions_manifest_with_metricsFiles/_restore_successful_conversion_snapshot.py
import src
"""
