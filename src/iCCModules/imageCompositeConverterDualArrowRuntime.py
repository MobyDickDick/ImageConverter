from __future__ import annotations


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
        write_validation_log_fn(["status=dual_arrow_badge_detection_failed_fallback_embedded_svg"])
    else:
        badge_params["variant_name"] = str(filename).rsplit(".", 1)[0]
        badge_params["base_name"] = str(base_name).upper()
        svg_content = generate_dual_arrow_badge_svg_fn(width, height, badge_params)
        write_validation_log_fn(["status=dual_arrow_badge_ok"])

    svg_rendered = render_svg_to_numpy_fn(svg_content, width, height)
    if svg_rendered is None:
        record_render_failure_fn(
            "dual_arrow_badge_final_render_failed",
            svg_content=svg_content,
            params_snapshot=badge_params if badge_params is not None else params,
        )
        return None

    write_attempt_artifacts_fn(svg_content, svg_rendered)
    return base_name, description, params, 1, calculate_error_fn(perc_img, svg_rendered)
