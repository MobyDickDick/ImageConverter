from src.iCCModules.imageCompositeConverterReachability import (
    aggregateNotReachableExitCodeImpl,
    classifyNotReachableImpl,
)


def test_reachability_classifier_exposes_stable_reason_report_and_exit_codes() -> None:
    cases = [
        ({"details": "stopped_due_to_stagnation"}, "stagnation", "NR001", 20),
        ({"details": "validation_time_budget_exceeded"}, "budget_exceeded", "NR002", 21),
        ({"reason": "aspect_ratio_mismatch"}, "dimension_violation", "NR003", 22),
        ({"status": "semantic_mismatch"}, "semantic_conflict", "NR004", 23),
    ]

    for evidence, reason, report_code, exit_code in cases:
        result = classifyNotReachableImpl(evidence)
        assert result["reason"] == reason
        assert result["report_code"] == report_code
        assert result["exit_code"] == exit_code


def test_reachability_precedence_and_unknown_fallback_are_deterministic() -> None:
    assert classifyNotReachableImpl({"details": "timeout after semantic conflict"})["reason"] == "semantic_conflict"
    assert classifyNotReachableImpl({"status": "unexpected_error"})["reason"] == "stagnation"
    assert aggregateNotReachableExitCodeImpl(
        [{"reason": "timeout"}, {"reason": "wrong dimensions"}]
    ) == 22
