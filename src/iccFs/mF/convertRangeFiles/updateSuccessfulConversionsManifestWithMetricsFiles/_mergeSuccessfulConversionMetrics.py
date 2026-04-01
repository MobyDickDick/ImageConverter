def mergeSuccessfulConversionMetrics(
    existing: dict[str, dict[str, object]],
    incoming: dict[str, dict[str, object]],
) -> dict[str, dict[str, object]]:
    merged = dict(existing or {})
    merged.update(incoming or {})
    return merged
