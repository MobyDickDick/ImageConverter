from __future__ import annotations


def runPreparedIterationModeImpl(
    *,
    mode: str,
    width: int,
    height: int,
    params: dict[str, object],
    stripe_strategy: dict[str, object] | None,
    semantic_mode_visual_override: bool,
    folder_path: str,
    img_path: str,
    filename: str,
    base_name: str,
    description: str,
    perc_img,
    perc_base_name: str,
    semantic_audit_row: dict[str, object] | None,
    max_iterations: int,
    badge_validation_rounds: int,
    debug_element_diff_dir: str | None,
    debug_ac0811_dir: str | None,
    write_validation_log_fn,
    write_attempt_artifacts_fn,
    record_render_failure_fn,
    run_semantic_badge_iteration_fn,
    run_dual_arrow_badge_iteration_fn,
    run_non_composite_iteration_fn,
    run_composite_iteration_fn,
    calculate_error_fn,
    print_fn,
) -> tuple[str, str, dict[str, object], int, float] | None:
    if mode == "semantic_badge":
        return run_semantic_badge_iteration_fn(
            width=width,
            height=height,
            perc_img=perc_img,
            perc_base_name=perc_base_name,
            filename=filename,
            base=base_name,
            description=description,
            params=params,
            semantic_audit_row=semantic_audit_row,
            badge_validation_rounds=badge_validation_rounds,
            debug_element_diff_dir=debug_element_diff_dir,
            debug_ac0811_dir=debug_ac0811_dir,
            write_attempt_artifacts_fn=write_attempt_artifacts_fn,
            write_validation_log_fn=write_validation_log_fn,
            record_render_failure_fn=record_render_failure_fn,
        )

    if mode == "dual_arrow_badge":
        return run_dual_arrow_badge_iteration_fn(
            perc_img=perc_img,
            filename=filename,
            base_name=base_name,
            description=description,
            params=params,
            width=width,
            height=height,
            write_validation_log_fn=write_validation_log_fn,
            record_render_failure_fn=record_render_failure_fn,
            write_attempt_artifacts_fn=write_attempt_artifacts_fn,
            calculate_error_fn=calculate_error_fn,
        )

    if mode != "composite":
        return run_non_composite_iteration_fn(
            mode=mode,
            params=params,
            stripe_strategy=stripe_strategy,
            semantic_mode_visual_override=semantic_mode_visual_override,
            width=width,
            height=height,
            base_name=base_name,
            description=description,
            perc_img=perc_img,
            img_path=img_path,
            print_fn=print_fn,
            write_validation_log_fn=write_validation_log_fn,
            record_render_failure_fn=record_render_failure_fn,
            write_attempt_artifacts_fn=write_attempt_artifacts_fn,
            calculate_error_fn=calculate_error_fn,
        )

    composite_result = run_composite_iteration_fn(
        max_iterations=max_iterations,
        width=width,
        height=height,
        params=params,
        folder_path=folder_path,
        target_img=perc_img,
        print_fn=print_fn,
        write_attempt_artifacts_fn=write_attempt_artifacts_fn,
        write_validation_log_fn=write_validation_log_fn,
        record_render_failure_fn=record_render_failure_fn,
    )
    if composite_result is None:
        return None
    if (
        isinstance(composite_result, tuple)
        and len(composite_result) >= 5
    ):
        return composite_result
    if (
        isinstance(composite_result, tuple)
        and len(composite_result) >= 2
    ):
        best_iter, best_error = composite_result[0], composite_result[1]
        return base_name, description, params, int(best_iter), float(best_error)
    return None
