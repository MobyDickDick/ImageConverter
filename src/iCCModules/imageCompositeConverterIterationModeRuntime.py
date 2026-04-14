"""Runtime helper for wiring iteration mode handlers used by runIterationPipeline."""

from __future__ import annotations

from typing import Any


class IterationModeRunners(dict):
    """Dictionary-like container for prepared iteration mode callables."""



def buildIterationModeRunnersImpl(
    *,
    np_module,
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
    validate_badge_by_elements_fn,
    prepare_semantic_badge_post_validation_fn,
    append_semantic_connector_expectation_log_fn,
    build_semantic_ok_validation_outcome_fn,
    build_semantic_ok_validation_log_lines_fn,
    semantic_quality_flags_fn,
    finalize_semantic_badge_run_fn,
    finalize_semantic_badge_iteration_result_fn,
    finalize_ac0223_badge_params_fn,
    render_svg_to_numpy_fn,
    calculate_error_fn,
    enforce_semantic_connector_expectation_fn,
    apply_redraw_variation_fn,
    print_fn,
    run_semantic_badge_iteration_fn,
    detect_dual_arrow_badge_params_fn,
    generate_dual_arrow_badge_svg_fn,
    run_dual_arrow_badge_iteration_fn,
    render_embedded_raster_svg_fn,
    build_gradient_stripe_svg_fn,
    build_gradient_stripe_validation_log_lines_fn,
    run_non_composite_iteration_fn,
    generate_composite_svg_fn,
    create_diff_image_fn,
    run_composite_iteration_fn,
) -> IterationModeRunners:
    """Build wrapped mode runners with stable dependency injection wiring."""

    def run_semantic_badge_iteration(**kwargs):
        return run_semantic_badge_iteration_fn(
            **kwargs,
            make_badge_params_fn=make_badge_params_fn,
            generate_badge_svg_fn=generate_badge_svg_fn,
            validate_semantic_description_alignment_fn=validate_semantic_description_alignment_fn,
            detect_semantic_primitives_fn=detect_semantic_primitives_fn,
            build_semantic_connector_debug_line_fn=build_semantic_connector_debug_line_fn,
            build_semantic_mismatch_console_lines_fn=build_semantic_mismatch_console_lines_fn,
            build_semantic_mismatch_validation_log_lines_fn=build_semantic_mismatch_validation_log_lines_fn,
            build_semantic_mismatch_outcome_fn=build_semantic_mismatch_outcome_fn,
            build_semantic_audit_log_lines_fn=build_semantic_audit_log_lines_fn,
            build_semantic_audit_record_kwargs_fn=build_semantic_audit_record_kwargs_fn,
            semantic_audit_record_fn=semantic_audit_record_fn,
            resolve_semantic_validation_debug_dir_fn=resolve_semantic_validation_debug_dir_fn,
            collect_semantic_badge_validation_logs_fn=lambda **log_kwargs: collect_semantic_badge_validation_logs_fn(
                **log_kwargs,
                validate_badge_by_elements_fn=validate_badge_by_elements_fn,
            ),
            prepare_semantic_badge_post_validation_fn=prepare_semantic_badge_post_validation_fn,
            append_semantic_connector_expectation_log_fn=append_semantic_connector_expectation_log_fn,
            build_semantic_ok_validation_outcome_fn=lambda **result_kwargs: build_semantic_ok_validation_outcome_fn(
                **result_kwargs,
                build_semantic_ok_validation_log_lines_fn=build_semantic_ok_validation_log_lines_fn,
            ),
            semantic_quality_flags_fn=semantic_quality_flags_fn,
            finalize_semantic_badge_run_fn=finalize_semantic_badge_run_fn,
            finalize_semantic_badge_iteration_result_fn=finalize_semantic_badge_iteration_result_fn,
            finalize_ac0223_badge_params_fn=finalize_ac0223_badge_params_fn,
            render_svg_to_numpy_fn=render_svg_to_numpy_fn,
            calculate_error_fn=calculate_error_fn,
            enforce_semantic_connector_expectation_fn=enforce_semantic_connector_expectation_fn,
            apply_redraw_variation_fn=apply_redraw_variation_fn,
            print_fn=print_fn,
        )

    def run_dual_arrow_badge_iteration(**kwargs):
        return run_dual_arrow_badge_iteration_fn(
            **kwargs,
            detect_dual_arrow_badge_params_fn=lambda img: detect_dual_arrow_badge_params_fn(img, np_module=np_module),
            generate_dual_arrow_badge_svg_fn=generate_dual_arrow_badge_svg_fn,
            render_embedded_raster_svg_fn=lambda: render_embedded_raster_svg_fn(kwargs["img_path"]),
            render_svg_to_numpy_fn=render_svg_to_numpy_fn,
        )

    def run_non_composite_iteration(**kwargs):
        return run_non_composite_iteration_fn(
            **kwargs,
            render_embedded_raster_svg_fn=render_embedded_raster_svg_fn,
            build_gradient_stripe_svg_fn=build_gradient_stripe_svg_fn,
            build_gradient_stripe_validation_log_lines_fn=build_gradient_stripe_validation_log_lines_fn,
            render_svg_to_numpy_fn=render_svg_to_numpy_fn,
        )

    def run_composite_iteration(**kwargs):
        return run_composite_iteration_fn(
            **kwargs,
            np_module=np_module,
            generate_composite_svg_fn=generate_composite_svg_fn,
            render_svg_to_numpy_fn=render_svg_to_numpy_fn,
            calculate_error_fn=calculate_error_fn,
            create_diff_image_fn=create_diff_image_fn,
        )

    return IterationModeRunners(
        run_semantic_badge_iteration=run_semantic_badge_iteration,
        run_dual_arrow_badge_iteration=run_dual_arrow_badge_iteration,
        run_non_composite_iteration=run_non_composite_iteration,
        run_composite_iteration=run_composite_iteration,
    )
