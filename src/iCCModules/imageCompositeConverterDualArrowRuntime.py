from __future__ import annotations

DUAL_ARROW_REVIEW_NORMALIZED_MSE_THRESHOLD = 0.045945679012345676


def _normalizedMse(target, rendered) -> float | None:
    try:
        delta = target.astype("float32") - rendered.astype("float32")
        mean_delta2 = float((delta * delta).sum(axis=2).mean())
    except (AttributeError, TypeError, ValueError, IndexError):
        return None
    return mean_delta2 / (3.0 * 255.0 * 255.0)


def runDualArrowBadgeIterationImpl(
    *,
    perc_img,
    filename: str,
    base_name: str,
    description: str,
    params: dict[str, object],
    width: int,
    height: int,
    detect_dual_arrow_badge_params_fn,
    generate_dual_arrow_badge_svg_fn,
    render_embedded_raster_svg_fn,
    write_validation_log_fn,
    render_svg_to_numpy_fn,
    record_render_failure_fn,
    write_attempt_artifacts_fn,
    calculate_error_fn,
) -> tuple[str, str, dict[str, object], int, float] | None:
    badge_params = detect_dual_arrow_badge_params_fn(perc_img)
    if badge_params is None:
        # Fallback to embedded raster if detection cannot robustly isolate
        # the dual-arrow primitives.
        svg_content = render_embedded_raster_svg_fn()
        validation_lines = ["status=dual_arrow_badge_detection_failed_fallback_embedded_svg"]
    else:
        badge_params["variant_name"] = str(filename).rsplit(".", 1)[0]
        badge_params["base_name"] = str(base_name).upper()
        svg_content = generate_dual_arrow_badge_svg_fn(width, height, badge_params)
        validation_lines = ["status=dual_arrow_badge_ok"]

    svg_rendered = render_svg_to_numpy_fn(svg_content, width, height)
    if svg_rendered is None:
        record_render_failure_fn(
            "dual_arrow_badge_final_render_failed",
            svg_content=svg_content,
            params_snapshot=badge_params if badge_params is not None else params,
        )
        return None

    normalized_mse = _normalizedMse(perc_img, svg_rendered)
    if (
        badge_params is not None
        and normalized_mse is not None
        and normalized_mse > DUAL_ARROW_REVIEW_NORMALIZED_MSE_THRESHOLD
        and badge_params.get("mask_runs")
    ):
        mask_params = dict(badge_params)
        mask_params["use_mask_runs"] = True
        mask_svg_content = generate_dual_arrow_badge_svg_fn(width, height, mask_params)
        mask_svg_rendered = render_svg_to_numpy_fn(mask_svg_content, width, height)
        mask_normalized_mse = _normalizedMse(perc_img, mask_svg_rendered)
        if mask_svg_rendered is not None and mask_normalized_mse is not None and mask_normalized_mse < normalized_mse:
            svg_content = mask_svg_content
            svg_rendered = mask_svg_rendered
            normalized_mse = mask_normalized_mse
            validation_lines.append("quality_refinement=mask_runs")

    if normalized_mse is not None:
        validation_lines.append(f"normalized_mse={normalized_mse:.8f}")
        if normalized_mse > DUAL_ARROW_REVIEW_NORMALIZED_MSE_THRESHOLD:
            validation_lines[0] = "status=dual_arrow_badge_quality_failed"
            validation_lines.append(
                "quality_reason=normalized_mse_above_review_gate:"
                f"{normalized_mse:.8f}>{DUAL_ARROW_REVIEW_NORMALIZED_MSE_THRESHOLD:.8f}"
            )
    write_validation_log_fn(validation_lines)
    write_attempt_artifacts_fn(svg_content, svg_rendered)
    return base_name, description, params, 1, calculate_error_fn(perc_img, svg_rendered)
