"""Quality-threshold helpers for convertRange quality-pass orchestration."""

from __future__ import annotations

import math

AUTO_ALLOWED_ERROR_FLOOR = 1.0


def resolveAllowedErrorPerPixelImpl(
    current_rows: list[dict[str, object]],
    cfg: dict[str, object],
    *,
    quality_sort_key_fn,
    successful_threshold_fn,
) -> tuple[float, str, float, float]:
    """Resolve the active quality threshold and its provenance.

    Returns `(allowed_error_per_pixel, source, successful_threshold, initial_threshold)`.
    """
    ranked_rows = sorted(current_rows, key=quality_sort_key_fn)
    first_cut = max(1, len(ranked_rows) // 3) if ranked_rows else 0
    initial_top_tercile = ranked_rows[:first_cut]
    initial_threshold = float(initial_top_tercile[-1]["error_per_pixel"]) if initial_top_tercile else float("inf")

    successful_threshold = float(successful_threshold_fn(current_rows))
    threshold_source = "successful-conversions-mean-plus-2std"
    if not math.isfinite(successful_threshold):
        successful_threshold = initial_threshold

    allowed_error_pp = max(AUTO_ALLOWED_ERROR_FLOOR, successful_threshold)
    cfg_value = cfg.get("allowed_error_per_pixel")
    if cfg_value is not None:
        try:
            allowed_error_pp = max(0.0, float(cfg_value))
            threshold_source = "manual-config"
        except (TypeError, ValueError):
            allowed_error_pp = successful_threshold

    return allowed_error_pp, threshold_source, successful_threshold, initial_threshold
