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


def _successful_conversion_snapshot_dir(reports_out_dir: str) -> Path:
    """Directory used to persist best-of artifacts for successful conversions."""
    return Path(reports_out_dir) / 'successful_conversions_bestlist'


def _successful_conversion_snapshot_paths(reports_out_dir: str, variant: str) -> dict[str, Path]:
    base_dir = _successful_conversion_snapshot_dir(reports_out_dir)
    base_dir.mkdir(parents=True, exist_ok=True)
    return {
        'svg': base_dir / f'{variant}.svg',
        'log': base_dir / f'{variant}_element_validation.log',
        'metrics': base_dir / f'{variant}.json',
    }


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


