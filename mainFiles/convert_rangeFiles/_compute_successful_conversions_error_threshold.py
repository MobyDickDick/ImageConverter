def _compute_successful_conversions_error_threshold(
    rows: list[dict[str, object]],
    successful_variants: list[str] | tuple[str, ...] | None = None,
) -> float:
    """Return mean(error_per_pixel) + 2*std(error_per_pixel) for successful rows.

    The successful set is sourced from ``successful_conversions.txt`` (via
    ``SUCCESSFUL_CONVERSIONS``) unless explicitly provided. Returns ``inf`` when
    no finite samples are available.
    """
    selected = {str(v).strip().upper() for v in (successful_variants or SUCCESSFUL_CONVERSIONS) if str(v).strip()}
    if not selected:
        return float("inf")

    values: list[float] = []
    for row in rows:
        variant = str(row.get("variant", "")).strip().upper()
        if variant not in selected:
            continue
        err = float(row.get("error_per_pixel", float("inf")))
        if math.isfinite(err):
            values.append(err)

    if not values:
        return float("inf")

    mean_val = float(statistics.fmean(values))
    std_val = float(statistics.pstdev(values)) if len(values) > 1 else 0.0
    return float(mean_val + 2.0 * std_val)
