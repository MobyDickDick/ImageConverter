"""AC08 adaptive lock helpers extracted from the converter monolith."""

from __future__ import annotations


def activateAc08AdaptiveLocksImpl(
    params: dict,
    logs: list[str],
    *,
    full_err: float,
    reason: str,
) -> bool:
    """Adaptive AC08 locks are disabled so semantic badge fitting stays unconstrained."""
    return False


def releaseAc08AdaptiveLocksImpl(
    params: dict,
    logs: list[str],
    *,
    reason: str,
    current_error: float,
) -> bool:
    """Adaptive AC08 lock release is disabled because there are no AC08 locks to release."""
    return False
