from __future__ import annotations


def buildSemanticMismatchOutcomeImpl(
    *,
    base_name: str,
    audit_base_name: str,
    filename: str,
    params: dict[str, object],
    perc_img,
    badge_params: dict[str, object],
    semantic_issues: list[str],
    semantic_audit_row: dict[str, object] | None,
    detect_semantic_primitives_fn,
    build_semantic_connector_debug_line_fn,
    build_semantic_mismatch_console_lines_fn,
    build_semantic_mismatch_validation_log_lines_fn,
    build_semantic_audit_log_lines_fn,
    build_semantic_audit_record_kwargs_fn,
    semantic_audit_record_fn,
) -> tuple[dict[str, object] | None, list[str], list[str]]:
    structural = detect_semantic_primitives_fn(perc_img, badge_params)
    connector_debug_line = build_semantic_connector_debug_line_fn(structural=structural)
    console_lines = build_semantic_mismatch_console_lines_fn(
        connector_debug_line=connector_debug_line,
        semantic_issues=semantic_issues,
    )
    if semantic_audit_row is not None:
        semantic_audit_row = semantic_audit_record_fn(
            base_name=audit_base_name,
            **build_semantic_audit_record_kwargs_fn(
                filename=filename,
                params=params,
                status="semantic_mismatch",
                mismatch_reasons=semantic_issues,
            ),
        )
    validation_lines = build_semantic_mismatch_validation_log_lines_fn(
        base_name=base_name,
        semantic_issues=semantic_issues,
        connector_debug_line=connector_debug_line,
        semantic_audit_lines=build_semantic_audit_log_lines_fn(
            semantic_audit_row,
            include_mismatch_reason=True,
        ),
    )
    return semantic_audit_row, console_lines, validation_lines
