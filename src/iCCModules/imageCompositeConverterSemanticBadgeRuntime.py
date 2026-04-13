from __future__ import annotations


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
    if badge_params is None:
        return None

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
    validation_logs = collect_semantic_badge_validation_logs_fn(
        perc_img=perc_img,
        badge_params=badge_params,
        badge_validation_rounds=badge_validation_rounds,
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
