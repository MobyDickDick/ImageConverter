def _successfulConversionMetricsAvailable(metrics: dict[str, object]) -> bool:
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
