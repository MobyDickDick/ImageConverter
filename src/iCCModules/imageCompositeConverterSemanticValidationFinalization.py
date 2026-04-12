from __future__ import annotations


def appendSemanticConnectorExpectationLogImpl(
    *,
    validation_logs: list[str],
    badge_params: dict[str, object],
) -> list[str]:
    result = list(validation_logs)
    if badge_params.get("arm_enabled"):
        result.append(
            "semantic-guard: Erwartete Arm-Geometrie bestätigt/wiederhergestellt (z.B. AC0812 links)."
        )
    return result


def buildSemanticOkValidationOutcomeImpl(
    *,
    base_name: str,
    filename: str,
    params: dict[str, object],
    semantic_audit_row: dict[str, object] | None,
    validation_logs: list[str],
    redraw_variation_logs: list[str],
    semantic_quality_flags_fn,
    semantic_audit_record_fn,
    build_semantic_audit_record_kwargs_fn,
    build_semantic_audit_log_lines_fn,
    build_semantic_ok_validation_log_lines_fn,
) -> tuple[dict[str, object] | None, list[str]]:
    updated_semantic_audit_row = semantic_audit_row
    if updated_semantic_audit_row is not None:
        updated_semantic_audit_row = semantic_audit_record_fn(
            base_name=base_name,
            **build_semantic_audit_record_kwargs_fn(
                filename=filename,
                params=params,
                status="semantic_ok",
            ),
        )

    quality_flags = semantic_quality_flags_fn(base_name, validation_logs)
    validation_lines = build_semantic_ok_validation_log_lines_fn(
        semantic_audit_lines=build_semantic_audit_log_lines_fn(
            updated_semantic_audit_row,
        ),
        quality_flags=quality_flags,
        redraw_variation_logs=redraw_variation_logs,
        validation_logs=validation_logs,
    )
    return updated_semantic_audit_row, validation_lines
