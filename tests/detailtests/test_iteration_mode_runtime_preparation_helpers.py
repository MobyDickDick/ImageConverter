from src.iCCModules import imageCompositeConverterIterationModeRuntimePreparation as helpers


def test_build_prepare_iteration_mode_runtime_bindings_for_run_kwargs_impl_maps_expected_keys():
    result = helpers.buildPrepareIterationModeRuntimeBindingsForRunKwargsImpl(
        build_prepare_iteration_mode_runtime_for_run_kwargs_fn="build_kwargs",
        prepare_iteration_mode_runtime_for_run_fn="prepare_runtime",
        np_module="np",
        action_cls="Action",
        params={"mode": "semantic_badge"},
        perception_image=[[1, 2]],
        stripe_strategy={"strategy": "global"},
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

    assert result["build_prepare_iteration_mode_runtime_for_run_kwargs_fn"] == "build_kwargs"
    assert result["prepare_iteration_mode_runtime_for_run_fn"] == "prepare_runtime"
    assert result["params"] == {"mode": "semantic_badge"}
    assert result["build_iteration_mode_runner_dependencies_fn"] == "build_deps"


def test_prepare_iteration_mode_runtime_bindings_impl_builds_kwargs_and_extracts_bindings():
    captured = {}

    def _build_kwargs(**kwargs):
        captured["build_kwargs"] = kwargs
        return {"prepared": True, "value": 7}

    def _prepare_runtime(**kwargs):
        captured["prepare_kwargs"] = kwargs
        return {
            "params": {"mode": "semantic_badge"},
            "semantic_mode_visual_override": "override",
            "mode_runners": {"semantic_badge": object()},
            "ignored": "value",
        }

    result = helpers.prepareIterationModeRuntimeBindingsImpl(
        build_prepare_iteration_mode_runtime_for_run_kwargs_fn=_build_kwargs,
        prepare_iteration_mode_runtime_for_run_fn=_prepare_runtime,
        build_prepare_iteration_mode_runtime_for_run_kwargs_kwargs={"alpha": 1, "beta": 2},
    )

    assert captured["build_kwargs"] == {"alpha": 1, "beta": 2}
    assert captured["prepare_kwargs"] == {"prepared": True, "value": 7}
    assert result["params"] == {"mode": "semantic_badge"}
    assert result["semantic_mode_visual_override"] == "override"
    assert sorted(result["mode_runners"].keys()) == ["semantic_badge"]


def test_prepare_iteration_mode_runtime_bindings_for_run_impl_builds_mode_setup_kwargs():
    captured = {}

    def _build_kwargs(**kwargs):
        captured["build_kwargs"] = kwargs
        return {"prepared": "kwargs"}

    def _prepare_runtime(**kwargs):
        captured["prepare_kwargs"] = kwargs
        return {
            "params": {"mode": "composite"},
            "semantic_mode_visual_override": None,
            "mode_runners": {"composite": object()},
        }

    result = helpers.prepareIterationModeRuntimeBindingsForRunImpl(
        build_prepare_iteration_mode_runtime_for_run_kwargs_fn=_build_kwargs,
        prepare_iteration_mode_runtime_for_run_fn=_prepare_runtime,
        np_module="np",
        action_cls="Action",
        params={"mode": "semantic_badge"},
        perception_image=[[1, 2]],
        stripe_strategy={"strategy": "global"},
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

    assert captured["prepare_kwargs"] == {"prepared": "kwargs"}
    assert captured["build_kwargs"]["params"] == {"mode": "semantic_badge"}
    assert captured["build_kwargs"]["build_iteration_mode_runner_dependencies_fn"] == "build_deps"
    assert result["params"] == {"mode": "composite"}
    assert sorted(result["mode_runners"].keys()) == ["composite"]


def test_prepare_iteration_mode_runtime_locals_for_run_impl_prepares_and_extracts_locals():
    captured = {}

    def _prepare_runtime_bindings_for_run(**kwargs):
        captured["prepare_kwargs"] = kwargs
        return {
            "params": {"mode": "semantic_badge"},
            "semantic_mode_visual_override": "override",
            "mode_runners": {"semantic_badge": object()},
        }

    def _extract_locals(*, iteration_mode_runtime_fields):
        captured["extract_fields"] = iteration_mode_runtime_fields
        return {"mode_runners": iteration_mode_runtime_fields["mode_runners"], "extra": True}

    result = helpers.prepareIterationModeRuntimeLocalsForRunImpl(
        prepare_iteration_mode_runtime_bindings_for_run_fn=_prepare_runtime_bindings_for_run,
        extract_iteration_mode_runtime_locals_fn=_extract_locals,
        prepare_iteration_mode_runtime_bindings_for_run_kwargs={"alpha": 1, "beta": 2},
    )

    assert captured["prepare_kwargs"] == {"alpha": 1, "beta": 2}
    assert captured["extract_fields"]["semantic_mode_visual_override"] == "override"
    assert sorted(result["mode_runners"].keys()) == ["semantic_badge"]
    assert result["extra"] is True
