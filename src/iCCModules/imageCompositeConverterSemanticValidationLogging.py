from __future__ import annotations


def buildSemanticMismatchValidationLogLinesImpl(
    *,
    base_name: str,
    semantic_issues: list[str],
    connector_debug_line: str,
    semantic_audit_lines: list[str],
) -> list[str]:
    return [
        "status=semantic_mismatch",
        f"best_attempt_svg={base_name}_failed.svg",
        connector_debug_line,
        *semantic_audit_lines,
        *[f"issue={issue}" for issue in semantic_issues],
    ]


def buildSemanticOkValidationLogLinesImpl(
    *,
    semantic_audit_lines: list[str],
    quality_flags: list[str],
    redraw_variation_logs: list[str],
    validation_logs: list[str],
) -> list[str]:
    return [
        "status=semantic_ok",
        *semantic_audit_lines,
        *quality_flags,
        *redraw_variation_logs,
        *validation_logs,
    ]
