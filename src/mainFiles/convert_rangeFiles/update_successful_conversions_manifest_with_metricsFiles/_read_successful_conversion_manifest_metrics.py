from src import image_composite_converter as _icc

globals().update(vars(_icc))

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
