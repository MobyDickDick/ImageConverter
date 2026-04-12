from __future__ import annotations

from src.iCCModules import imageCompositeConverterSemanticValidationLogging as helpers


def test_build_semantic_mismatch_validation_log_lines_impl_contains_expected_fields() -> None:
    lines = helpers.buildSemanticMismatchValidationLogLinesImpl(
        base_name="AC0811_S",
        semantic_issues=["issue_a", "issue_b"],
        connector_debug_line="semantic_connector_classification=vertical",
        semantic_audit_lines=["semantic_audit_status=semantic_mismatch"],
    )

    assert lines[0] == "status=semantic_mismatch"
    assert lines[1] == "best_attempt_svg=AC0811_S_failed.svg"
    assert "semantic_connector_classification=vertical" in lines
    assert "semantic_audit_status=semantic_mismatch" in lines
    assert "issue=issue_a" in lines
    assert "issue=issue_b" in lines


def test_build_semantic_ok_validation_log_lines_impl_keeps_order() -> None:
    lines = helpers.buildSemanticOkValidationLogLinesImpl(
        semantic_audit_lines=["semantic_audit_status=semantic_ok"],
        quality_flags=["quality_flag=example"],
        redraw_variation_logs=["redraw_variation=none"],
        validation_logs=["semantic-guard: Textmodus aktiv"],
    )

    assert lines == [
        "status=semantic_ok",
        "semantic_audit_status=semantic_ok",
        "quality_flag=example",
        "redraw_variation=none",
        "semantic-guard: Textmodus aktiv",
    ]
