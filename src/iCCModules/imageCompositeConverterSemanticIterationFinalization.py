from __future__ import annotations


def finalizeSemanticBadgeRunImpl(
    *,
    base: str,
    desc: str,
    perc_base_name: str,
    filename: str,
    width: int,
    height: int,
    badge_params: dict[str, object],
    params: dict[str, object],
    semantic_audit_row: dict[str, object] | None,
    semantic_ok_validation_lines: list[str],
    perc_img,
    write_validation_log_fn,
    finalize_semantic_badge_iteration_result_fn,
):
    write_validation_log_fn(semantic_ok_validation_lines)

    semantic_badge_result = finalize_semantic_badge_iteration_result_fn(
        base_name=str(perc_base_name),
        filename=filename,
        width=width,
        height=height,
        badge_params=badge_params,
        params=params,
        semantic_audit_row=semantic_audit_row,
        target_img=perc_img,
    )
    if semantic_badge_result is None:
        return None

    result_params, semantic_badge_error = semantic_badge_result
    return base, desc, result_params, 1, semantic_badge_error
