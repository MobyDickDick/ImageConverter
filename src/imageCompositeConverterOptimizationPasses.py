"""Extracted quality-pass selection/iteration helpers for imageCompositeConverter."""

from __future__ import annotations

import math
import statistics


def qualitySortKeyImpl(row: dict[str, object]) -> float:
    value = float(row.get("error_per_pixel", float("inf")))
    if math.isfinite(value):
        return value
    return float("inf")


def computeSuccessfulConversionsErrorThresholdImpl(
    rows: list[dict[str, object]],
    successful_variants: list[str] | tuple[str, ...] | None = None,
) -> float:
    """Return mean(error_per_pixel) + 2*std(error_per_pixel) for successful rows."""
    selected = {str(v).strip().upper() for v in (successful_variants or ()) if str(v).strip()}
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


def selectMiddleLowerTercileImpl(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    if len(rows) < 3:
        return []

    ranked = sorted(rows, key=qualitySortKeyImpl)
    first_cut = max(1, len(ranked) // 3)
    return ranked[first_cut:]


def selectOpenQualityCasesImpl(
    rows: list[dict[str, object]],
    *,
    allowed_error_per_pixel: float,
    skip_variants: set[str] | None = None,
) -> list[dict[str, object]]:
    """Return unresolved quality cases sorted from worst to best."""
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

    return sorted(open_rows, key=qualitySortKeyImpl, reverse=True)


def iterationStrategyForPassImpl(pass_idx: int, base_iterations: int) -> tuple[int, int]:
    """Adaptive per-pass search budget for unresolved quality cases."""
    p = max(1, int(pass_idx))
    base = max(1, int(base_iterations))
    phase = (p - 1) % 3

    if phase == 0:
        return base + p, 6 + p
    if phase == 1:
        return base + 24 + (p * 2), 7 + p
    return base + 48 + (p * 3), 8 + p


def adaptiveIterationBudgetForQualityRowImpl(row: dict[str, object], planned_budget: int) -> int:
    """Tune per-row iteration budget using convergence/plateau quality signals."""
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
