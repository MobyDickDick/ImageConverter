from src.iCCModules import imageCompositeConverterIterationModeSetup as helpers


def test_build_prepare_iteration_mode_runtime_for_run_kwargs_impl_includes_dependency_module_map():
    kwargs = helpers.buildPrepareIterationModeRuntimeForRunKwargsImpl(
        np_module="np",
        action_cls="Action",
        params={"mode": "semantic_badge"},
        perception_image=[[1]],
        stripe_strategy={"name": "none"},
        looks_like_elongated_foreground_rect_fn="elongated",
        semantic_visual_override_helpers="visual_override",
        iteration_mode_dependency_setup_helpers="dependency_setup",
        iteration_mode_runtime_helpers="mode_runtime",
        iteration_orchestration_helpers="orchestration",
        iteration_context_helpers="context",
        semantic_mismatch_reporting_helpers="mismatch_reporting",
        semantic_validation_logging_helpers="validation_logging",
        semantic_mismatch_runtime_helpers="mismatch_runtime",
        semantic_audit_logging_helpers="audit_logging",
        semantic_audit_runtime_helpers="audit_runtime",
        semantic_validation_context_helpers="validation_context",
        semantic_validation_runtime_helpers="validation_runtime",
        semantic_post_validation_helpers="post_validation",
        semantic_validation_finalization_helpers="validation_finalization",
        semantic_iteration_finalization_helpers="iteration_finalization",
        semantic_ac0223_runtime_helpers="ac0223_runtime",
        dual_arrow_badge_helpers="dual_arrow_badge",
        dual_arrow_runtime_helpers="dual_arrow_runtime",
        gradient_stripe_strategy_helpers="gradient_stripe",
        non_composite_runtime_helpers="non_composite",
        conversion_composite_helpers="conversion_composite",
        semantic_badge_runtime_helpers="semantic_badge_runtime",
        build_iteration_mode_runner_dependencies_fn="build_deps",
        semantic_audit_record_fn="audit_record",
        semantic_quality_flags_fn="quality_flags",
        render_embedded_raster_svg_fn="render_embedded",
        print_fn="print",
    )

    assert kwargs["params"] == {"mode": "semantic_badge"}
    assert kwargs["mode_dependency_helper_modules"]["semantic_mismatch_runtime_helpers"] == "mismatch_runtime"
    assert kwargs["mode_dependency_helper_modules"]["build_iteration_mode_runner_dependencies_fn"] == "build_deps"
    assert kwargs["render_embedded_raster_svg_fn"] == "render_embedded"
