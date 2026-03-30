def _restore_successful_conversion_snapshot(variant: str, svg_out_dir: str, reports_out_dir: str) -> bool:
    """Restore the previous best conversion for ``variant`` if a snapshot exists."""
    snapshot_paths = _successful_conversion_snapshot_paths(reports_out_dir, variant)
    restored = False

    target_svg = Path(svg_out_dir) / f'{variant}.svg'
    if snapshot_paths['svg'].exists():
        target_svg.parent.mkdir(parents=True, exist_ok=True)
        target_svg.write_text(snapshot_paths['svg'].read_text(encoding='utf-8'), encoding='utf-8')
        restored = True

    target_log = Path(reports_out_dir) / f'{variant}_element_validation.log'
    if snapshot_paths['log'].exists():
        target_log.write_text(snapshot_paths['log'].read_text(encoding='utf-8'), encoding='utf-8')
        restored = True

    return restored
""" End move to File mainFiles/convert_rangeFiles/update_successful_conversions_manifest_with_metricsFiles/_restore_successful_conversion_snapshot.py """


""" Start move to File mainFiles/convert_rangeFiles/update_successful_conversions_manifest_with_metricsFiles/_store_successful_conversion_snapshot.py
import src
"""
def _store_successful_conversion_snapshot(variant: str, metrics: dict[str, object], svg_out_dir: str, reports_out_dir: str) -> None:
    """Persist the current best conversion artifacts for later rollback/restoration."""
    snapshot_paths = _successful_conversion_snapshot_paths(reports_out_dir, variant)
    target_svg = Path(svg_out_dir) / f'{variant}.svg'
    if target_svg.exists():
        snapshot_paths['svg'].write_text(target_svg.read_text(encoding='utf-8'), encoding='utf-8')

    target_log = Path(reports_out_dir) / f'{variant}_element_validation.log'
    if target_log.exists():
        snapshot_paths['log'].write_text(target_log.read_text(encoding='utf-8'), encoding='utf-8')

    snapshot_paths['metrics'].write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True),
        encoding='utf-8',
    )
""" End move to File mainFiles/convert_rangeFiles/update_successful_conversions_manifest_with_metricsFiles/_store_successful_conversion_snapshot.py """


""" Start move to File mainFiles/convert_rangeFiles/update_successful_conversions_manifest_with_metricsFiles/_is_successful_conversion_candidate_better.py
import src
"""
def _is_successful_conversion_candidate_better(
    previous_metrics: dict[str, object] | None,
    candidate_metrics: dict[str, object],
) -> bool:
    """Accept a new best-list candidate only when it improves quality."""
    if not _successful_conversion_metrics_available(candidate_metrics):
        return False
    if not previous_metrics or not _successful_conversion_metrics_available(previous_metrics):
        return True

    previous_status = str(previous_metrics.get('status', '')).strip().lower()
    candidate_status = str(candidate_metrics.get('status', '')).strip().lower()
    if previous_status == 'semantic_ok' and candidate_status != 'semantic_ok':
        return False
    if previous_status != 'semantic_ok' and candidate_status == 'semantic_ok':
        return True

    improved, _decision, _prev_error, _new_error, _prev_delta, _new_delta = _evaluate_quality_pass_candidate(
        previous_metrics,
        candidate_metrics,
    )
    return improved
""" End move to File mainFiles/convert_rangeFiles/update_successful_conversions_manifest_with_metricsFiles/_is_successful_conversion_candidate_better.py """


""" Start move to File mainFiles/convert_rangeFiles/update_successful_conversions_manifest_with_metricsFiles/_merge_successful_conversion_metrics.py
import src
"""
def _merge_successful_conversion_metrics(
    baseline: dict[str, object],
    override: dict[str, object],
) -> dict[str, object]:
    """Merge ``override`` into ``baseline`` while keeping row-level defaults."""
    merged = dict(baseline)
    for key, value in override.items():
        if key == 'variant':
            continue
        merged[key] = value
    merged['variant'] = str(override.get('variant', baseline.get('variant', ''))).strip().upper()
    return merged
""" End move to File mainFiles/convert_rangeFiles/update_successful_conversions_manifest_with_metricsFiles/_merge_successful_conversion_metrics.py """


""" Start move to File mainFiles/convert_rangeFiles/update_successful_conversions_manifest_with_metricsFiles/_format_successful_conversion_manifest_line.py
import src
"""
