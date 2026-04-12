from __future__ import annotations

from src.iCCModules import imageCompositeConverterSemanticMismatchRuntime as helpers


def test_build_semantic_mismatch_outcome_impl_with_audit_row() -> None:
    def _detect(_img, _params):
        return {"connector_orientation": "vertical"}

    def _connector_line(*, structural):
        return f"connector={structural['connector_orientation']}"

    def _console_lines(*, connector_debug_line, semantic_issues):
        return [connector_debug_line, *semantic_issues]

    def _validation_lines(*, base_name, semantic_issues, connector_debug_line, semantic_audit_lines):
        return [base_name, connector_debug_line, *semantic_audit_lines, *semantic_issues]

    def _audit_lines(_row, *, include_mismatch_reason):
        return [f"audit_mismatch={include_mismatch_reason}"]

    def _audit_kwargs(*, filename, params, status, mismatch_reasons):
        return {
            "filename": filename,
            "status": status,
            "semantic_elements": list(params.get("elements", [])),
            "mismatch_reasons": mismatch_reasons,
        }

    def _audit_record(*, base_name, **kwargs):
        return {"base_name": base_name, **kwargs}

    semantic_audit_row, console_lines, validation_lines = helpers.buildSemanticMismatchOutcomeImpl(
        base_name="AC0811_S",
        audit_base_name="AC0811",
        filename="AC0811_S.jpg",
        params={"elements": ["line"]},
        perc_img=object(),
        badge_params={"cx": 1.0},
        semantic_issues=["issue-1"],
        semantic_audit_row={"status": "semantic_pending"},
        detect_semantic_primitives_fn=_detect,
        build_semantic_connector_debug_line_fn=_connector_line,
        build_semantic_mismatch_console_lines_fn=_console_lines,
        build_semantic_mismatch_validation_log_lines_fn=_validation_lines,
        build_semantic_audit_log_lines_fn=_audit_lines,
        build_semantic_audit_record_kwargs_fn=_audit_kwargs,
        semantic_audit_record_fn=_audit_record,
    )

    assert semantic_audit_row == {
        "base_name": "AC0811",
        "filename": "AC0811_S.jpg",
        "status": "semantic_mismatch",
        "semantic_elements": ["line"],
        "mismatch_reasons": ["issue-1"],
    }
    assert console_lines == ["connector=vertical", "issue-1"]
    assert validation_lines == ["AC0811_S", "connector=vertical", "audit_mismatch=True", "issue-1"]


def test_build_semantic_mismatch_outcome_impl_without_audit_row() -> None:
    semantic_audit_row, console_lines, validation_lines = helpers.buildSemanticMismatchOutcomeImpl(
        base_name="AC0813_L",
        audit_base_name="AC0813",
        filename="AC0813_L.jpg",
        params={},
        perc_img=object(),
        badge_params={},
        semantic_issues=["issue-x"],
        semantic_audit_row=None,
        detect_semantic_primitives_fn=lambda _img, _params: {},
        build_semantic_connector_debug_line_fn=lambda **_kwargs: "connector=unknown",
        build_semantic_mismatch_console_lines_fn=lambda **kwargs: [kwargs["connector_debug_line"]],
        build_semantic_mismatch_validation_log_lines_fn=lambda **kwargs: [kwargs["base_name"], *kwargs["semantic_audit_lines"]],
        build_semantic_audit_log_lines_fn=lambda _row, **_kwargs: [],
        build_semantic_audit_record_kwargs_fn=lambda **_kwargs: {},
        semantic_audit_record_fn=lambda **_kwargs: {"unexpected": True},
    )

    assert semantic_audit_row is None
    assert console_lines == ["connector=unknown"]
    assert validation_lines == ["AC0813_L"]
