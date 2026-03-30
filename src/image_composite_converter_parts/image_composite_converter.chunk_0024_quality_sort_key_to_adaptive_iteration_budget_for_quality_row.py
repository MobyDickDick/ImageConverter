def _quality_sort_key(row: dict[str, object]) -> float:
    value = float(row.get("error_per_pixel", float("inf")))
    if math.isfinite(value):
        return value
    return float("inf")




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


def _select_middle_lower_tercile(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    if len(rows) < 3:
        return []

    ranked = sorted(rows, key=_quality_sort_key)
    first_cut = max(1, len(ranked) // 3)
    return ranked[first_cut:]


def _select_open_quality_cases(
    rows: list[dict[str, object]],
    *,
    allowed_error_per_pixel: float,
    skip_variants: set[str] | None = None,
) -> list[dict[str, object]]:
    """Return unresolved quality cases sorted from worst to best.

    "Open" means the case is finite, not explicitly skipped, and still above the
    accepted quality threshold.
    """
    skips = {str(v).upper() for v in (skip_variants or set()) if str(v).strip()}
    open_rows: list[dict[str, object]] = []
    for row in rows:
        err = float(row.get("error_per_pixel", float("inf")))
        if not math.isfinite(err):
            continue
        variant = str(row.get("variant", "")).upper()
        if variant and variant in skips:
            continue
        if math.isfinite(allowed_error_per_pixel) and err <= allowed_error_per_pixel:
            continue
        open_rows.append(row)

    return sorted(open_rows, key=_quality_sort_key, reverse=True)


def _iteration_strategy_for_pass(pass_idx: int, base_iterations: int) -> tuple[int, int]:
    """Adaptive per-pass search budget for unresolved quality cases."""
    p = max(1, int(pass_idx))
    base = max(1, int(base_iterations))
    phase = (p - 1) % 3

    if phase == 0:
        return base + p, 6 + p
    if phase == 1:
        return base + 24 + (p * 2), 7 + p
    return base + 48 + (p * 3), 8 + p


def _adaptive_iteration_budget_for_quality_row(row: dict[str, object], planned_budget: int) -> int:
    """Tune per-row iteration budget using convergence/plateau quality signals.

    Heuristic goals:
    - plateau reached clearly before budget end -> reduce budget next pass
    - max-iterations hit or best-iter near budget end -> increase budget
    """
    budget = max(1, int(planned_budget))
    convergence = str(row.get("convergence", "") or "").strip().lower()
    best_iter_raw = row.get("best_iter", 0)
    try:
        best_iter = max(0, int(best_iter_raw))
    except (TypeError, ValueError):
        best_iter = 0

    usage_ratio = (best_iter / budget) if budget > 0 else 0.0

    if convergence == "plateau":
        if usage_ratio <= 0.35:
            return max(1, int(round(budget * 0.60)))
        if usage_ratio <= 0.55:
            return max(1, int(round(budget * 0.80)))
        return budget

    if convergence == "max_iterations" or usage_ratio >= 0.95:
        return max(1, int(round(budget * 1.35)))
    if usage_ratio >= 0.80:
        return max(1, int(round(budget * 1.15)))
    return budget


