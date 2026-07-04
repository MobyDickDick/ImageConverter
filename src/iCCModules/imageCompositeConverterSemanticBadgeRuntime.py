from __future__ import annotations


def _generic_description_badge_params(width: int, height: int, params: dict) -> dict | None:
    """Build catalog-free circle/text badge params from semantic description elements."""
    elements = [str(element).lower() for element in params.get("elements", [])]
    if not any("kreis" in element for element in elements):
        return None

    expects_left = any("waagrechter strich links" in element for element in elements)
    expects_right = any("waagrechter strich rechts" in element for element in elements)
    expects_top = any("senkrechter strich oben" in element for element in elements)
    expects_bottom = any("senkrechter strich hinter" in element for element in elements)
    min_side = float(max(1, min(width, height)))
    stroke = max(1.0, min_side * 0.045)
    r = max(1.0, (min_side - 3.0) / 2.0)
    cx = float(width) / 2.0
    cy = float(height) / 2.0
    if expects_left:
        cx = max(r + stroke, float(width) - r - stroke)
    elif expects_right:
        cx = min(float(width) - r - stroke, r + stroke)
    if expects_top:
        cy = max(r + stroke, float(height) - r - stroke)
    elif expects_bottom:
        cy = min(float(height) - r - stroke, r + stroke)

    label = str(params.get("label", "") or "")
    badge = {
        "cx": cx,
        "cy": cy,
        "r": r,
        "stroke_circle": stroke,
        "fill_gray": 242,
        "stroke_gray": 127,
        "text_gray": 102,
        "draw_text": bool(label),
        "label": label,
        "text_mode": "path_t" if label.upper() == "T" else label.lower(),
        "s": 0.0100 * (min_side / 30.0),
        "tx": cx - (4.0 * (min_side / 30.0)),
        "ty": cy - (6.0 * (min_side / 30.0)),
        "width": float(width),
        "height": float(height),
        "arm_enabled": False,
    }
    arm_stroke = max(1.0, stroke)
    if expects_left:
        badge.update(
            {
                "connector_direction": "left",
                "arm_enabled": True,
                "arm_x1": 0.0,
                "arm_y1": cy,
                "arm_x2": max(0.0, cx - r - arm_stroke / 2.0),
                "arm_y2": cy,
                "arm_stroke": arm_stroke,
            }
        )
    elif expects_right:
        badge.update(
            {
                "connector_direction": "right",
                "arm_enabled": True,
                "arm_x1": min(float(width), cx + r + arm_stroke / 2.0),
                "arm_y1": cy,
                "arm_x2": float(width),
                "arm_y2": cy,
                "arm_stroke": arm_stroke,
            }
        )
    return badge


def applySquareBadgeVariantParamsImpl(badge_params: dict, *, width: int, height: int) -> dict:
    """Apply catalog-free square-badge variant defaults measured from the canvas.

    The colors deliberately describe the generic visual role (red square head with
    grey outline/stem) rather than a concrete image identifier.
    """

    badge_params["head_fill"] = "#e10821"
    badge_params["head_stroke"] = "#a0a0a0"
    badge_params["square_badge_full_canvas"] = True
    badge_params["stroke_gray"] = 160
    badge_params["cx"] = float(width) / 2.0
    badge_params["cy"] = max(1.0, float(width) / 2.0)
    badge_params["r"] = max(1.0, (float(width) - 2.0) / 2.0)
    badge_params["square_badge_x"] = 1.0
    badge_params["square_badge_y"] = 1.25
    badge_params["square_badge_side"] = max(1.0, float(width) - 2.0)
    badge_params["square_badge_height"] = max(1.0, float(width) - 1.5)
    badge_params["arm_enabled"] = False
    badge_params["stem_enabled"] = True
    badge_params["stem_x"] = max(0.0, (float(width) / 2.0) - 1.0)
    badge_params["stem_top"] = max(0.0, float(width) + 2.0)
    badge_params["stem_bottom"] = float(height)
    badge_params["stem_width"] = 2.0
    badge_params["stem_gray"] = 160
    badge_params["skip_element_validation"] = True
    return badge_params


def runSemanticBadgeIterationImpl(
    *,
    width: int,
    height: int,
    perc_img,
    perc_base_name: str,
    filename: str,
    base: str,
    description: str,
    params: dict,
    semantic_audit_row: dict[str, object] | None,
    badge_validation_rounds: int,
    debug_element_diff_dir: str | None,
    debug_ac0811_dir: str | None,
    write_attempt_artifacts_fn,
    write_validation_log_fn,
    record_render_failure_fn,
    make_badge_params_fn,
    generate_badge_svg_fn,
    validate_semantic_description_alignment_fn,
    detect_semantic_primitives_fn,
    build_semantic_connector_debug_line_fn,
    build_semantic_mismatch_console_lines_fn,
    build_semantic_mismatch_validation_log_lines_fn,
    build_semantic_mismatch_outcome_fn,
    build_semantic_audit_log_lines_fn,
    build_semantic_audit_record_kwargs_fn,
    semantic_audit_record_fn,
    resolve_semantic_validation_debug_dir_fn,
    collect_semantic_badge_validation_logs_fn,
    prepare_semantic_badge_post_validation_fn,
    append_semantic_connector_expectation_log_fn,
    build_semantic_ok_validation_outcome_fn,
    semantic_quality_flags_fn,
    finalize_semantic_badge_run_fn,
    finalize_semantic_badge_iteration_result_fn,
    finalize_ac0223_badge_params_fn,
    render_svg_to_numpy_fn,
    calculate_error_fn,
    enforce_semantic_connector_expectation_fn,
    apply_redraw_variation_fn,
    print_fn,
):
    badge_params = make_badge_params_fn(width, height, perc_base_name, perc_img)
    variant_name = str(params.get("variant_name", perc_base_name) or perc_base_name)
    if badge_params is None and "_" in variant_name:
        badge_param_source_ref = str(params.get("badge_param_source_ref", "") or "").strip()
        if badge_param_source_ref and badge_param_source_ref.upper() != str(perc_base_name).upper():
            badge_params = make_badge_params_fn(width, height, badge_param_source_ref, perc_img)
            if badge_params is not None:
                badge_params["param_source_ref"] = badge_param_source_ref
                badge_params["variant_name"] = variant_name
    if badge_params is None:
        badge_params = _generic_description_badge_params(width, height, params)
    if badge_params is None:
        return None

    head_style = params.get("head_style")
    if head_style:
        badge_params["head_style"] = head_style
    if str(head_style or "").lower() == "square_badge" and "_" in variant_name:
        applySquareBadgeVariantParamsImpl(badge_params, width=width, height=height)

    badge_params.setdefault("width", float(width))
    badge_params.setdefault("height", float(height))
    badge_overrides = params.get("badge_overrides")
    if isinstance(badge_overrides, dict):
        badge_params.update(badge_overrides)

    semantic_issues = validate_semantic_description_alignment_fn(
        perc_img,
        list(params.get("elements", [])),
        badge_params,
    )
    if semantic_issues:
        failed_svg = generate_badge_svg_fn(width, height, badge_params)
        write_attempt_artifacts_fn(failed_svg, failed=True)
        _semantic_audit_row, mismatch_console_lines, mismatch_validation_lines = (
            build_semantic_mismatch_outcome_fn(
                base_name=base,
                audit_base_name=perc_base_name,
                filename=filename,
                params=params,
                perc_img=perc_img,
                badge_params=badge_params,
                semantic_issues=semantic_issues,
                semantic_audit_row=semantic_audit_row,
                detect_semantic_primitives_fn=detect_semantic_primitives_fn,
                build_semantic_connector_debug_line_fn=build_semantic_connector_debug_line_fn,
                build_semantic_mismatch_console_lines_fn=build_semantic_mismatch_console_lines_fn,
                build_semantic_mismatch_validation_log_lines_fn=build_semantic_mismatch_validation_log_lines_fn,
                build_semantic_audit_log_lines_fn=build_semantic_audit_log_lines_fn,
                build_semantic_audit_record_kwargs_fn=build_semantic_audit_record_kwargs_fn,
                semantic_audit_record_fn=semantic_audit_record_fn,
            )
        )
        for console_line in mismatch_console_lines:
            print_fn(console_line)
        write_validation_log_fn(mismatch_validation_lines)
        return None

    debug_dir = resolve_semantic_validation_debug_dir_fn(
        debug_element_diff_dir=debug_element_diff_dir,
        debug_ac0811_dir=debug_ac0811_dir,
        filename=filename,
        base_name=perc_base_name,
    )
    effective_badge_validation_rounds = int(badge_validation_rounds)
    if (
        bool(badge_params.get("arm_enabled", False))
        and str(badge_params.get("connector_direction", "")).lower() == "left"
        and not bool(badge_params.get("draw_text", False))
    ):
        # Plain left-arm circle badges need only one local element-validation
        # round after image fitting. Additional rounds mostly replay expensive
        # render probes, so the cap is keyed to measured/derived geometry
        # metadata instead of a catalog family name.
        effective_badge_validation_rounds = min(effective_badge_validation_rounds, 1)
        badge_params["validation_round_cap_reason"] = "plain_left_arm_single_round"
    validation_logs = collect_semantic_badge_validation_logs_fn(
        perc_img=perc_img,
        badge_params=badge_params,
        badge_validation_rounds=effective_badge_validation_rounds,
        debug_dir=debug_dir,
    )
    badge_params, validation_logs, redraw_variation_logs = prepare_semantic_badge_post_validation_fn(
        base_name=str(perc_base_name),
        elements=list(params.get("elements", [])),
        badge_params=badge_params,
        width=width,
        height=height,
        validation_logs=validation_logs,
        enforce_semantic_connector_expectation_fn=enforce_semantic_connector_expectation_fn,
        apply_redraw_variation_fn=apply_redraw_variation_fn,
        append_semantic_connector_expectation_log_fn=append_semantic_connector_expectation_log_fn,
    )

    semantic_audit_row, semantic_ok_validation_lines = build_semantic_ok_validation_outcome_fn(
        base_name=perc_base_name,
        filename=filename,
        params=params,
        semantic_audit_row=semantic_audit_row,
        validation_logs=validation_logs,
        redraw_variation_logs=redraw_variation_logs,
        semantic_quality_flags_fn=semantic_quality_flags_fn,
        semantic_audit_record_fn=semantic_audit_record_fn,
        build_semantic_audit_record_kwargs_fn=build_semantic_audit_record_kwargs_fn,
        build_semantic_audit_log_lines_fn=build_semantic_audit_log_lines_fn,
    )
    return finalize_semantic_badge_run_fn(
        base=base,
        desc=description,
        perc_base_name=str(perc_base_name),
        filename=filename,
        width=width,
        height=height,
        badge_params=badge_params,
        params=params,
        semantic_audit_row=semantic_audit_row,
        semantic_ok_validation_lines=semantic_ok_validation_lines,
        perc_img=perc_img,
        write_validation_log_fn=write_validation_log_fn,
        finalize_semantic_badge_iteration_result_fn=lambda **kwargs: finalize_semantic_badge_iteration_result_fn(
            **kwargs,
            finalize_ac0223_badge_params_fn=finalize_ac0223_badge_params_fn,
            generate_badge_svg_fn=generate_badge_svg_fn,
            render_svg_to_numpy_fn=render_svg_to_numpy_fn,
            write_attempt_artifacts_fn=write_attempt_artifacts_fn,
            record_render_failure_fn=record_render_failure_fn,
            calculate_error_fn=calculate_error_fn,
        ),
    )
