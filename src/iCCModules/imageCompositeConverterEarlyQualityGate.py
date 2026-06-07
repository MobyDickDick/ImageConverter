"""Early quality-gate policy for avoiding predictably futile full conversions."""

from __future__ import annotations

import math
import os

DEFAULT_PROBE_ITERATIONS = 3
DEFAULT_THRESHOLD_MULTIPLIER = 8.0


def _finiteNonNegative(value: object) -> float | None:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(numeric) or numeric < 0.0:
        return None
    return numeric


def _finitePositive(value: object) -> float | None:
    numeric = _finiteNonNegative(value)
    return numeric if numeric is not None and numeric > 0.0 else None


def resolveEarlyQualityGateImpl(
    cfg: dict[str, object],
    historical_rows: list[dict[str, object]],
    *,
    successful_threshold_fn,
    environ: dict[str, str] | None = None,
) -> dict[str, object]:
    """Resolve a conservative probe gate from persisted report data.

    The persisted ``allowed_error_per_pixel`` is preferred. If it is absent,
    previously successful conversion rows provide the baseline. Without either
    source the gate stays disabled, because a fresh output directory has no
    trustworthy quality history yet.
    """
    env = os.environ if environ is None else environ
    raw_gate_cfg = cfg.get("early_abort", {})
    gate_cfg = raw_gate_cfg if isinstance(raw_gate_cfg, dict) else {}

    enabled = bool(gate_cfg.get("enabled", True))
    env_enabled = str(env.get("ICC_EARLY_QUALITY_ABORT", "")).strip().lower()
    if env_enabled:
        enabled = env_enabled not in {"0", "false", "no", "off"}

    baseline = _finitePositive(cfg.get("allowed_error_per_pixel"))
    source = "quality-config"
    if baseline is None:
        baseline = _finitePositive(successful_threshold_fn(historical_rows))
        source = "successful-conversions-mean-plus-2std"

    probe_iterations = gate_cfg.get("probe_iterations", DEFAULT_PROBE_ITERATIONS)
    multiplier = gate_cfg.get("threshold_multiplier", DEFAULT_THRESHOLD_MULTIPLIER)
    if str(env.get("ICC_EARLY_QUALITY_PROBE_ITERATIONS", "")).strip():
        probe_iterations = env["ICC_EARLY_QUALITY_PROBE_ITERATIONS"]
    if str(env.get("ICC_EARLY_QUALITY_MULTIPLIER", "")).strip():
        multiplier = env["ICC_EARLY_QUALITY_MULTIPLIER"]

    try:
        probe_iterations = max(1, int(probe_iterations))
    except (TypeError, ValueError):
        probe_iterations = DEFAULT_PROBE_ITERATIONS
    parsed_multiplier = _finiteNonNegative(multiplier)
    if parsed_multiplier is None or parsed_multiplier < 1.0:
        parsed_multiplier = DEFAULT_THRESHOLD_MULTIPLIER

    abort_threshold = baseline * parsed_multiplier if baseline is not None else float("inf")
    return {
        "enabled": bool(enabled and baseline is not None),
        "probe_iterations": probe_iterations,
        "baseline_error_per_pixel": baseline if baseline is not None else float("inf"),
        "threshold_multiplier": parsed_multiplier,
        "abort_error_per_pixel": abort_threshold,
        "source": source if baseline is not None else "unavailable",
    }


def shouldAbortAfterProbeImpl(
    row: dict[str, object] | None,
    *,
    requested_iterations: int,
    gate: dict[str, object],
) -> bool:
    """Return whether a finite probe result is clearly outside the success band."""
    if not bool(gate.get("enabled", False)) or row is None:
        return False
    probe_iterations = max(1, int(gate.get("probe_iterations", DEFAULT_PROBE_ITERATIONS)))
    if int(requested_iterations) <= probe_iterations:
        return False
    error = _finiteNonNegative(row.get("error_per_pixel"))
    threshold = _finiteNonNegative(gate.get("abort_error_per_pixel"))
    return error is not None and threshold is not None and error > threshold
