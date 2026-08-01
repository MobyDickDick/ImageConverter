"""Quality-threshold helpers for convertRange quality-pass orchestration."""

from __future__ import annotations

import math

AUTO_ALLOWED_ERROR_FLOOR = 1.0

# Conservative defaults on the raw squared RGB-distance scale.  A mean_delta2
# of 300 corresponds to an RMSE of sqrt(300 / 3) == 10 intensity levels per
# colour channel (on the 0..255 scale).  The std limit additionally rejects
# strongly concentrated errors that a tolerable mean can otherwise hide.
RECOMMENDED_MAX_MEAN_DELTA2 = 300.0
RECOMMENDED_MAX_STD_DELTA2 = 3_000.0


def resolvePixelErrorAcceptanceImpl(cfg: dict[str, object]) -> tuple[float | None, float | None]:
    """Read optional mean/std pixel-delta limits from the quality config.

    For each pixel, ``delta2 = dR² + dG² + dB²``. ``mean_delta2`` is the mean
    of those values and ``std_delta2`` their standard deviation. Missing, malformed,
    negative, or non-finite limits disable only the corresponding criterion.
    """
    raw = cfg.get("pixel_error_acceptance", {})
    if not isinstance(raw, dict):
        return None, None

    def _limit(key: str) -> float | None:
        try:
            value = float(raw.get(key))
        except (TypeError, ValueError):
            return None
        return value if math.isfinite(value) and value >= 0.0 else None

    return _limit("max_mean_delta2"), _limit("max_std_delta2")


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
