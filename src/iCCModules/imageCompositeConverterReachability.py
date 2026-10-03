"""Canonical, deterministic classification of unreachable conversion results."""

from __future__ import annotations

from collections.abc import Mapping


REACHABILITY_SCHEMA_VERSION = "image_converter_reachability_v1"
REASONS = ("stagnation", "budget_exceeded", "dimension_violation", "semantic_conflict")
REPORT_CODES = {
    "stagnation": "NR001",
    "budget_exceeded": "NR002",
    "dimension_violation": "NR003",
    "semantic_conflict": "NR004",
}
EXIT_CODES = {
    "stagnation": 20,
    "budget_exceeded": 21,
    "dimension_violation": 22,
    "semantic_conflict": 23,
}

# The ordering is intentional and is also used when a batch contains several
# causes.  A violated hard constraint is more specific than a search timeout;
# a semantic contradiction is more specific than ordinary lack of progress.
_PRECEDENCE = ("dimension_violation", "semantic_conflict", "budget_exceeded", "stagnation")
_TOKENS = {
    "dimension_violation": ("dimension", "aspect_ratio", "canvas_size", "size_mismatch"),
    "semantic_conflict": ("semantic", "contradiction", "description_conflict"),
    "budget_exceeded": ("budget", "timeout", "timed_out", "time_limit"),
    "stagnation": ("stagnation", "plateau", "no_progress", "no_result", "conversion_failed"),
}


def classifyNotReachableImpl(evidence: Mapping[str, object] | None) -> dict[str, object]:
    """Normalize heterogeneous failure evidence to the public P1 contract.

    Unknown failures use ``stagnation`` as the conservative fallback: the
    search ended without a reachable result, but no hard constraint, semantic
    conflict, or exhausted budget was demonstrated.
    """

    values = evidence or {}
    explicit = str(values.get("reachability_reason", "")).strip().lower()
    if explicit in REASONS:
        reason = explicit
    else:
        haystack = " ".join(str(value).strip().lower() for value in values.values())
        reason = next(
            (candidate for candidate in _PRECEDENCE if any(token in haystack for token in _TOKENS[candidate])),
            "stagnation",
        )
    return {
        "schema_version": REACHABILITY_SCHEMA_VERSION,
        "reason": reason,
        "report_code": REPORT_CODES[reason],
        "exit_code": EXIT_CODES[reason],
    }


def aggregateNotReachableExitCodeImpl(rows: list[Mapping[str, object]]) -> int:
    """Return zero for a clean batch, otherwise the deterministic highest-priority code."""

    classified = [classifyNotReachableImpl(row) for row in rows]
    if not classified:
        return 0
    reasons = {str(item["reason"]) for item in classified}
    reason = next(candidate for candidate in _PRECEDENCE if candidate in reasons)
    return EXIT_CODES[reason]
