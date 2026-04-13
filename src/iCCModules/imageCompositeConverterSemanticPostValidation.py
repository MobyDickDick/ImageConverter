from __future__ import annotations


def prepareSemanticBadgePostValidationImpl(
    *,
    base_name: str,
    elements: list[object],
    badge_params: dict[str, object],
    width: int,
    height: int,
    validation_logs: list[str],
    enforce_semantic_connector_expectation_fn,
    apply_redraw_variation_fn,
    append_semantic_connector_expectation_log_fn,
) -> tuple[dict[str, object], list[str], list[str]]:
    post_guard_badge_params = enforce_semantic_connector_expectation_fn(
        base_name,
        list(elements),
        badge_params,
        width,
        height,
    )
    post_redraw_badge_params, redraw_variation_logs = apply_redraw_variation_fn(
        post_guard_badge_params,
        width,
        height,
    )
    post_validation_logs = append_semantic_connector_expectation_log_fn(
        validation_logs=validation_logs,
        badge_params=post_redraw_badge_params,
    )
    return post_redraw_badge_params, post_validation_logs, redraw_variation_logs
