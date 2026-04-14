from src.iCCModules import imageCompositeConverterIterationModeDependencies as helpers


def test_build_iteration_mode_runner_dependencies_impl_maps_all_runtime_hooks() -> None:
    marker = object()

    result = helpers.buildIterationModeRunnerDependenciesImpl(
        np_module=marker,
        make_badge_params_fn=marker,
        generate_badge_svg_fn=marker,
        validate_semantic_description_alignment_fn=marker,
        detect_semantic_primitives_fn=marker,
        build_semantic_connector_debug_line_fn=marker,
        build_semantic_mismatch_console_lines_fn=marker,
        build_semantic_mismatch_validation_log_lines_fn=marker,
        build_semantic_mismatch_outcome_fn=marker,
        build_semantic_audit_log_lines_fn=marker,
        build_semantic_audit_record_kwargs_fn=marker,
        semantic_audit_record_fn=marker,
        resolve_semantic_validation_debug_dir_fn=marker,
        collect_semantic_badge_validation_logs_fn=marker,
        validate_badge_by_elements_fn=marker,
        prepare_semantic_badge_post_validation_fn=marker,
        append_semantic_connector_expectation_log_fn=marker,
        build_semantic_ok_validation_outcome_fn=marker,
        build_semantic_ok_validation_log_lines_fn=marker,
        semantic_quality_flags_fn=marker,
        finalize_semantic_badge_run_fn=marker,
        finalize_semantic_badge_iteration_result_fn=marker,
        finalize_ac0223_badge_params_fn=marker,
        render_svg_to_numpy_fn=marker,
        calculate_error_fn=marker,
        enforce_semantic_connector_expectation_fn=marker,
        apply_redraw_variation_fn=marker,
        print_fn=marker,
        run_semantic_badge_iteration_fn=marker,
        detect_dual_arrow_badge_params_fn=marker,
        generate_dual_arrow_badge_svg_fn=marker,
        run_dual_arrow_badge_iteration_fn=marker,
        render_embedded_raster_svg_fn=marker,
        build_gradient_stripe_svg_fn=marker,
        build_gradient_stripe_validation_log_lines_fn=marker,
        run_non_composite_iteration_fn=marker,
        generate_composite_svg_fn=marker,
        create_diff_image_fn=marker,
        run_composite_iteration_fn=marker,
    )

    assert len(result) == 39
    assert set(result.values()) == {marker}
    assert result["run_composite_iteration_fn"] is marker
    assert result["resolve_semantic_validation_debug_dir_fn"] is marker
