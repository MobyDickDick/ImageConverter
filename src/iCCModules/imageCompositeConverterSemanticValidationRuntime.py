from __future__ import annotations

import copy


def buildSemanticTextModeValidationLogLineImpl(*, draw_text: bool, text_mode: object) -> str:
    if not draw_text:
        return "semantic-guard: Text bewusst deaktiviert (plain-ring Familie ohne Buchstabe)."
    return "semantic-guard: Textmodus aktiv (" + str(text_mode if text_mode is not None else "unknown") + ")."


def collectSemanticBadgeValidationLogsImpl(
    *,
    perc_img,
    badge_params: dict[str, object],
    badge_validation_rounds: int,
    debug_dir: str | None,
    validate_badge_by_elements_fn,
) -> list[str]:
    validation_logs: list[str] = [
        buildSemanticTextModeValidationLogLineImpl(
            draw_text=bool(badge_params.get("draw_text", False)),
            text_mode=badge_params.get("text_mode", "unknown"),
        )
    ]
    validation_logs.extend(
        validate_badge_by_elements_fn(
            perc_img,
            badge_params,
            max_rounds=max(1, int(badge_validation_rounds)),
            debug_out_dir=debug_dir,
        )
    )
    return validation_logs


def finalizeSemanticBadgeIterationResultImpl(
    *,
    base_name: str,
    filename: str,
    width: int,
    height: int,
    badge_params: dict[str, object],
    params: dict[str, object],
    semantic_audit_row: dict[str, object] | None,
    target_img,
    finalize_ac0223_badge_params_fn,
    generate_badge_svg_fn,
    render_svg_to_numpy_fn,
    write_attempt_artifacts_fn,
    record_render_failure_fn,
    calculate_error_fn,
) -> tuple[dict[str, object], float] | None:
    finalized_badge_params = finalize_ac0223_badge_params_fn(
        base_name=base_name,
        filename=filename,
        width=width,
        height=height,
        badge_params=badge_params,
    )
    svg_content = generate_badge_svg_fn(width, height, finalized_badge_params)
    svg_rendered = render_svg_to_numpy_fn(svg_content, width, height)
    if svg_rendered is None:
        record_render_failure_fn(
            "semantic_badge_final_render_failed",
            svg_content=svg_content,
            params_snapshot=finalized_badge_params,
        )
        return None
    write_attempt_artifacts_fn(svg_content, svg_rendered)
    result_params = params
    if semantic_audit_row is not None:
        result_params = copy.deepcopy(params)
        result_params["semantic_audit"] = semantic_audit_row
    return result_params, calculate_error_fn(target_img, svg_rendered)
