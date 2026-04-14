from types import SimpleNamespace

from src.iCCModules import imageCompositeConverterIterationModeDependencySetup as helpers


def test_build_iteration_mode_runner_dependencies_for_run_impl_uses_expected_runtime_hooks() -> None:
    marker = object()
    captured_kwargs = {}

    def fake_build_iteration_mode_runner_dependencies_fn(**kwargs):
        captured_kwargs.update(kwargs)
        return {"wired": marker}

    action_cls = SimpleNamespace(
        make_badge_params=marker,
        generate_badge_svg=marker,
        validate_semantic_description_alignment=marker,
        _detect_semantic_primitives=marker,
        validate_badge_by_elements=marker,
        render_svg_to_numpy=marker,
        calculate_error=marker,
        _enforce_semantic_connector_expectation=marker,
        apply_redraw_variation=marker,
        generate_composite_svg=marker,
        create_diff_image=marker,
    )

    result = helpers.buildIterationModeRunnerDependenciesForRunImpl(
        np_module=marker,
        action_cls=action_cls,
        semantic_mismatch_reporting_helpers=SimpleNamespace(
            buildSemanticConnectorDebugLineImpl=marker,
            buildSemanticMismatchConsoleLinesImpl=marker,
        ),
        semantic_validation_logging_helpers=SimpleNamespace(
            buildSemanticMismatchValidationLogLinesImpl=marker,
            buildSemanticOkValidationLogLinesImpl=marker,
        ),
        semantic_mismatch_runtime_helpers=SimpleNamespace(
            buildSemanticMismatchOutcomeImpl=marker,
        ),
        semantic_audit_logging_helpers=SimpleNamespace(
            buildSemanticAuditLogLinesImpl=marker,
        ),
        semantic_audit_runtime_helpers=SimpleNamespace(
            buildSemanticAuditRecordKwargsImpl=marker,
        ),
        semantic_validation_context_helpers=SimpleNamespace(
            resolveSemanticValidationDebugDirImpl=marker,
            buildNonCompositeGradientStripeValidationLogLinesImpl=marker,
        ),
        semantic_validation_runtime_helpers=SimpleNamespace(
            collectSemanticBadgeValidationLogsImpl=marker,
            finalizeSemanticBadgeIterationResultImpl=marker,
        ),
        semantic_post_validation_helpers=SimpleNamespace(
            prepareSemanticBadgePostValidationImpl=marker,
        ),
        semantic_validation_finalization_helpers=SimpleNamespace(
            appendSemanticConnectorExpectationLogImpl=marker,
            buildSemanticOkValidationOutcomeImpl=marker,
        ),
        semantic_iteration_finalization_helpers=SimpleNamespace(
            finalizeSemanticBadgeRunImpl=marker,
        ),
        semantic_ac0223_runtime_helpers=SimpleNamespace(
            finalizeAc0223BadgeParamsImpl=marker,
        ),
        dual_arrow_badge_helpers=SimpleNamespace(
            detectDualArrowBadgeParamsFromImageImpl=marker,
            generateDualArrowBadgeSvgImpl=marker,
        ),
        dual_arrow_runtime_helpers=SimpleNamespace(
            runDualArrowBadgeIterationImpl=marker,
        ),
        gradient_stripe_strategy_helpers=SimpleNamespace(
            buildGradientStripeSvgImpl=marker,
        ),
        non_composite_runtime_helpers=SimpleNamespace(
            runNonCompositeIterationImpl=marker,
        ),
        conversion_composite_helpers=SimpleNamespace(
            runCompositeIterationImpl=marker,
        ),
        semantic_badge_runtime_helpers=SimpleNamespace(
            runSemanticBadgeIterationImpl=marker,
        ),
        semantic_audit_record_fn=marker,
        semantic_quality_flags_fn=marker,
        render_embedded_raster_svg_fn=marker,
        print_fn=marker,
        build_iteration_mode_runner_dependencies_fn=fake_build_iteration_mode_runner_dependencies_fn,
    )

    assert result == {"wired": marker}
    assert len(captured_kwargs) == 39
    assert set(captured_kwargs.values()) == {marker}
