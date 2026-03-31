def _readSuccessfulConversionManifestMetrics(manifest_path: Path) -> dict[str, dict[str, object]]:
    """Load persisted best-list metrics keyed by variant."""
    if not manifest_path.exists():
        return {}

    rows: dict[str, dict[str, object]] = {}
    for raw_line in manifest_path.read_text(encoding='utf-8').splitlines():
        variant, metrics = _parseSuccessfulConversionManifestLine(raw_line)
        if variant:
            rows[variant] = metrics
    return rows
