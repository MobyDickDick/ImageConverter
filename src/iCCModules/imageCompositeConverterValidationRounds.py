"""Validation-round safety caps for semantic badge conversion."""

from __future__ import annotations

import os

DEFAULT_MAX_BADGE_VALIDATION_ROUNDS = 12


def resolveMaxBadgeValidationRoundsImpl(override: str | int | None = None) -> int:
    """Return the hard cap for element-validation rounds.

    The value is intentionally small because element validation already has
    stagnation detection. Large accidental values (for example reusing a global
    iteration budget such as 600) create misleading logs and long-running
    conversion passes without adding useful search breadth.
    """

    raw_value = (
        str(override)
        if override is not None
        else os.environ.get("ICC_MAX_BADGE_VALIDATION_ROUNDS", "")
    ).strip()
    if raw_value:
        try:
            return max(1, int(raw_value))
        except ValueError:
            pass
    return DEFAULT_MAX_BADGE_VALIDATION_ROUNDS


def clampBadgeValidationRoundsImpl(
    requested_rounds: int | str,
    *,
    max_rounds: int | str | None = None,
) -> tuple[int, bool, int]:
    """Clamp requested badge-validation rounds to the configured hard cap.

    Returns ``(effective_rounds, capped, requested_rounds)`` so callers can log
    a clear guard message when an oversized value was reduced.
    """

    try:
        requested = max(1, int(requested_rounds))
    except (TypeError, ValueError):
        requested = 1
    cap = resolveMaxBadgeValidationRoundsImpl(max_rounds)
    effective = min(requested, cap)
    return effective, effective != requested, requested
