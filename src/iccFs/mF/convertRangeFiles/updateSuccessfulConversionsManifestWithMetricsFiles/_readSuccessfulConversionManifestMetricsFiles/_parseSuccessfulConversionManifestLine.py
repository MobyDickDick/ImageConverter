def parseSuccessfulConversionManifestLine(raw_line: str) -> tuple[str, dict[str, object]]:
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
