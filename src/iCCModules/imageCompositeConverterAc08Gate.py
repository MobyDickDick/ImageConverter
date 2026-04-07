"""AC08 success-gate status formatting helpers."""

from __future__ import annotations


AC08_SUCCESS_GATE_CRITERIA_ORDER: tuple[str, ...] = (
    "criterion_no_new_batch_aborts",
    "criterion_no_accepted_regressions",
    "criterion_validation_rounds_recorded",
    "criterion_regression_set_improved",
    "criterion_stable_families_not_worse",
)


def emitAc08SuccessGateStatusImpl(
    ac08_success_gate: dict[str, object] | None,
    *,
    print_fn,
) -> None:
    """Print AC08 gate status in a single stable place.

    This keeps the convertRange orchestration focused on pipeline sequencing
    while preserving the historical console output contract used by operators
    and tests.
    """

    if ac08_success_gate is None:
        return

    failed_criteria = [
        key for key in AC08_SUCCESS_GATE_CRITERIA_ORDER if not bool(ac08_success_gate.get(key, False))
    ]
    mean_rounds = float(ac08_success_gate.get("mean_validation_rounds_per_file", 0.0))
    if failed_criteria:
        print_fn(
            "[WARN] AC08 success gate failed: "
            + ", ".join(failed_criteria)
            + f" (mean_validation_rounds_per_file={mean_rounds:.3f})"
        )
        return

    print_fn(f"[INFO] AC08 success gate passed (mean_validation_rounds_per_file={mean_rounds:.3f}).")
