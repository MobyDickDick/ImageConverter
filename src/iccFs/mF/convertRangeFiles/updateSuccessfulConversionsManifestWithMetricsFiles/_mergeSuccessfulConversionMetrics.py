def mergeSuccessfulConversionMetrics(
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
