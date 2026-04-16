from src.iCCModules import imageCompositeConverterIterationRunPreparation as helpers


def test_build_prepare_iteration_input_runtime_for_run_kwargs_impl_maps_all_fields() -> None:
    marker = object()
    kwargs = helpers.buildPrepareIterationInputRuntimeForRunKwargsImpl(
        img_path="images/AC0800_L.jpg",
        csv_path="descriptions.csv",
        perception_cls=marker,
        reflection_cls=str,
        detect_gradient_stripe_strategy_fn=marker,
        build_pending_semantic_audit_row_fn=marker,
        should_create_semantic_audit_for_base_name_fn=marker,
        get_base_name_from_file_fn=marker,
        build_semantic_audit_record_kwargs_fn=marker,
        semantic_audit_record_fn=marker,
        np_module=marker,
        print_fn=print,
    )

    assert kwargs["img_path"] == "images/AC0800_L.jpg"
    assert kwargs["csv_path"] == "descriptions.csv"
    assert kwargs["perception_cls"] is marker
    assert kwargs["semantic_audit_record_fn"] is marker
    assert kwargs["print_fn"] is print


def test_build_prepare_iteration_runtime_callbacks_for_run_kwargs_impl_maps_all_fields() -> None:
    marker = object()
    kwargs = helpers.buildPrepareIterationRuntimeCallbacksForRunKwargsImpl(
        filename="AC0800_L.jpg",
        params={"mode": "semantic_badge"},
        reports_out_dir="reports",
        svg_out_dir="svg",
        diff_out_dir="diff",
        target_img=marker,
        width=128,
        height=64,
        run_seed=1,
        pass_seed_offset=2,
        time_ns_fn=marker,
        render_svg_to_numpy_fn=marker,
        create_diff_image_fn=marker,
        cv2_module=marker,
        iteration_setup_helpers=marker,
        iteration_runtime_helpers=marker,
        print_fn=print,
    )

    assert kwargs["filename"] == "AC0800_L.jpg"
    assert kwargs["params"]["mode"] == "semantic_badge"
    assert kwargs["run_seed"] == 1
    assert kwargs["pass_seed_offset"] == 2
    assert kwargs["print_fn"] is print


def test_prepare_iteration_input_runtime_for_run_impl_returns_none_when_inputs_missing() -> None:
    calls: list[str] = []

    def _prepare_iteration_inputs(**_kwargs):
        calls.append("prepare")
        return None

    result = helpers.prepareIterationInputRuntimeForRunImpl(
        prepare_iteration_inputs_fn=_prepare_iteration_inputs,
        extract_iteration_input_bindings_fn=lambda **_kwargs: {},
        extract_iteration_input_runtime_fields_fn=lambda **_kwargs: {},
        prepare_iteration_inputs_kwargs={"img_path": "x"},
    )

    assert result is None
    assert calls == ["prepare"]


def test_prepare_iteration_runtime_callbacks_for_run_impl_wires_extraction_sequence() -> None:
    def _prepare_iteration_runtime(**kwargs):
        assert kwargs["filename"] == "AC0800_L.jpg"
        return {"runtime": "state"}

    def _extract_runtime_bindings(**kwargs):
        assert kwargs["iteration_runtime_state"] == {"runtime": "state"}
        return {"bindings": "ok"}

    def _extract_runtime_callbacks(**kwargs):
        assert kwargs["iteration_runtime_bindings"] == {"bindings": "ok"}
        return {"base_name": "AC0800_L", "write_validation_log": object()}

    result = helpers.prepareIterationRuntimeCallbacksForRunImpl(
        prepare_iteration_runtime_fn=_prepare_iteration_runtime,
        extract_iteration_runtime_bindings_fn=_extract_runtime_bindings,
        extract_iteration_runtime_callbacks_fn=_extract_runtime_callbacks,
        prepare_iteration_runtime_kwargs={"filename": "AC0800_L.jpg"},
    )

    assert result["base_name"] == "AC0800_L"


def test_prepare_run_iteration_pipeline_locals_impl_merges_all_runtime_sections() -> None:
    marker_img = object()

    class _Perception:
        img = marker_img

    def _prepare_input_runtime(**kwargs):
        assert kwargs == {"input": "kwargs"}
        return {"input_runtime": "fields"}

    def _extract_input_runtime_locals(**kwargs):
        assert kwargs["iteration_input_runtime_fields"] == {"input_runtime": "fields"}
        return {
            "filename": "AC0800_L.jpg",
            "params": {"mode": "semantic_badge"},
            "perception": _Perception(),
            "width": 64,
            "height": 32,
            "stripe_strategy": "adaptive",
        }

    def _build_runtime_kwargs(**kwargs):
        assert kwargs["filename"] == "AC0800_L.jpg"
        assert kwargs["params"] == {"mode": "semantic_badge"}
        assert kwargs["target_img"] is marker_img
        assert kwargs["width"] == 64
        assert kwargs["height"] == 32
        assert kwargs["extra"] == "runtime"
        return {"runtime": "kwargs"}

    def _prepare_runtime_callbacks(**kwargs):
        assert kwargs["prepare_iteration_runtime_kwargs"] == {"runtime": "kwargs"}
        assert kwargs["prepare_flag"] == "runtime"
        return {"callbacks": "fields"}

    def _extract_runtime_callback_locals(**kwargs):
        assert kwargs["iteration_runtime_callbacks"] == {"callbacks": "fields"}
        return {"write_validation_log": object()}

    def _build_mode_kwargs(**kwargs):
        assert kwargs["params"] == {"mode": "semantic_badge"}
        assert kwargs["perception_image"] is marker_img
        assert kwargs["stripe_strategy"] == "adaptive"
        assert kwargs["extra"] == "mode"
        return {"mode": "kwargs"}

    def _prepare_mode_locals(**kwargs):
        assert kwargs == {
            "prepare_iteration_mode_runtime_bindings_for_run_kwargs": {"mode": "kwargs"},
            "mode_flag": "locals",
        }
        return {"mode_locals": "ok"}

    def _extract_run_locals(**kwargs):
        assert kwargs["iteration_mode_runtime_locals"] == {"mode_locals": "ok"}
        return {"merged": "locals"}

    result = helpers.prepareRunIterationPipelineLocalsImpl(
        prepare_iteration_input_runtime_for_run_fn=_prepare_input_runtime,
        extract_iteration_input_runtime_locals_fn=_extract_input_runtime_locals,
        prepare_iteration_runtime_callbacks_for_run_fn=_prepare_runtime_callbacks,
        extract_iteration_runtime_callback_locals_fn=_extract_runtime_callback_locals,
        prepare_iteration_mode_runtime_locals_for_run_fn=_prepare_mode_locals,
        extract_run_iteration_pipeline_locals_fn=_extract_run_locals,
        prepare_iteration_input_runtime_for_run_kwargs={"input": "kwargs"},
        prepare_iteration_runtime_callbacks_for_run_kwargs_builder_fn=_build_runtime_kwargs,
        prepare_iteration_runtime_callbacks_for_run_shared_kwargs={"extra": "runtime"},
        prepare_iteration_runtime_callbacks_for_run_impl_kwargs={"prepare_flag": "runtime"},
        prepare_iteration_mode_runtime_locals_for_run_kwargs_builder_fn=_build_mode_kwargs,
        prepare_iteration_mode_runtime_locals_for_run_shared_kwargs={"extra": "mode"},
        prepare_iteration_mode_runtime_locals_for_run_impl_kwargs={"mode_flag": "locals"},
    )

    assert result == {"merged": "locals"}


def test_build_prepare_run_iteration_pipeline_locals_kwargs_impl_maps_all_fields() -> None:
    marker = object()
    kwargs = helpers.buildPrepareRunIterationPipelineLocalsKwargsImpl(
        prepare_iteration_input_runtime_for_run_fn=marker,
        extract_iteration_input_runtime_locals_fn=marker,
        prepare_iteration_runtime_callbacks_for_run_fn=marker,
        extract_iteration_runtime_callback_locals_fn=marker,
        prepare_iteration_mode_runtime_locals_for_run_fn=marker,
        extract_run_iteration_pipeline_locals_fn=marker,
        prepare_iteration_input_runtime_for_run_kwargs={"input": "kwargs"},
        prepare_iteration_runtime_callbacks_for_run_kwargs_builder_fn=marker,
        prepare_iteration_runtime_callbacks_for_run_shared_kwargs={"runtime": "shared"},
        prepare_iteration_runtime_callbacks_for_run_impl_kwargs={"runtime": "impl"},
        prepare_iteration_mode_runtime_locals_for_run_kwargs_builder_fn=marker,
        prepare_iteration_mode_runtime_locals_for_run_shared_kwargs={"mode": "shared"},
        prepare_iteration_mode_runtime_locals_for_run_impl_kwargs={"mode": "impl"},
    )

    assert kwargs["prepare_iteration_input_runtime_for_run_fn"] is marker
    assert kwargs["prepare_iteration_input_runtime_for_run_kwargs"] == {"input": "kwargs"}
    assert kwargs["prepare_iteration_runtime_callbacks_for_run_shared_kwargs"] == {"runtime": "shared"}
    assert kwargs["prepare_iteration_runtime_callbacks_for_run_impl_kwargs"] == {"runtime": "impl"}
    assert kwargs["prepare_iteration_mode_runtime_locals_for_run_shared_kwargs"] == {"mode": "shared"}
    assert kwargs["prepare_iteration_mode_runtime_locals_for_run_impl_kwargs"] == {"mode": "impl"}


def test_build_prepare_run_iteration_pipeline_locals_kwargs_for_run_impl_builds_nested_context() -> None:
    marker = object()

    class _Action:
        render_svg_to_numpy = marker
        create_diff_image = marker

    class _RunPreparation:
        prepareIterationInputRuntimeForRunImpl = marker
        prepareIterationRuntimeCallbacksForRunImpl = marker
        buildPrepareIterationRuntimeCallbacksForRunKwargsImpl = marker

    class _Bindings:
        extractIterationInputRuntimeLocalsImpl = marker
        extractIterationRuntimeCallbackLocalsImpl = marker
        extractIterationRuntimeCallbacksImpl = marker
        extractRunIterationPipelineLocalsImpl = marker
        extractIterationInputRuntimeFieldsImpl = marker
        extractIterationModeRuntimeLocalsImpl = marker

    class _Initialization:
        prepareIterationRuntimeImpl = marker
        extractIterationRuntimeBindingsImpl = marker

    class _ModeRuntimePreparation:
        prepareIterationModeRuntimeLocalsForRunImpl = marker
        buildPrepareIterationModeRuntimeBindingsForRunKwargsImpl = marker
        prepareIterationModeRuntimeBindingsForRunImpl = marker

    class _IterationPreparation:
        prepareIterationInputsImpl = marker

    class _IterationContext:
        extractIterationInputBindingsImpl = marker

    class _GradientStripe:
        detectGradientStripeStrategyImpl = marker

    class _SemanticAuditBootstrap:
        buildPendingSemanticAuditRowImpl = marker

    class _SemanticAuditRuntime:
        shouldCreateSemanticAuditForBaseNameImpl = marker
        buildSemanticAuditRecordKwargsImpl = marker

    class _ModeSetup:
        buildPrepareIterationModeRuntimeForRunKwargsImpl = marker

    class _ModePreparation:
        prepareIterationModeRuntimeForRunImpl = marker

    class _ModeDependencyHelpers:
        buildIterationModeRunnerDependenciesImpl = marker

    kwargs = helpers.buildPrepareRunIterationPipelineLocalsKwargsForRunImpl(
        img_path="images/AC0800_L.jpg",
        csv_path="descriptions.csv",
        reports_out_dir="reports",
        svg_out_dir="svg",
        diff_out_dir="diff",
        run_seed=1,
        pass_seed_offset=2,
        action_cls=_Action,
        perception_cls=marker,
        reflection_cls=marker,
        get_base_name_from_file_fn=marker,
        semantic_audit_record_fn=marker,
        semantic_quality_flags_fn=marker,
        looks_like_elongated_foreground_rect_fn=marker,
        render_embedded_raster_svg_fn=marker,
        np_module=marker,
        cv2_module=marker,
        print_fn=print,
        time_ns_fn=marker,
        iteration_run_preparation_helpers=_RunPreparation,
        iteration_bindings_helpers=_Bindings,
        iteration_initialization_helpers=_Initialization,
        iteration_setup_helpers=marker,
        iteration_runtime_helpers=marker,
        iteration_mode_runtime_preparation_helpers=_ModeRuntimePreparation,
        iteration_mode_setup_helpers=_ModeSetup,
        iteration_mode_preparation_helpers=_ModePreparation,
        iteration_mode_dependency_setup_helpers=marker,
        iteration_mode_dependency_helpers=_ModeDependencyHelpers,
        iteration_mode_runtime_helpers=marker,
        iteration_orchestration_helpers=marker,
        iteration_context_helpers=_IterationContext,
        iteration_preparation_helpers=_IterationPreparation,
        gradient_stripe_strategy_helpers=_GradientStripe,
        semantic_audit_bootstrap_helpers=_SemanticAuditBootstrap,
        semantic_audit_logging_helpers=marker,
        semantic_audit_runtime_helpers=_SemanticAuditRuntime,
        semantic_mismatch_reporting_helpers=marker,
        semantic_validation_logging_helpers=marker,
        semantic_mismatch_runtime_helpers=marker,
        semantic_validation_context_helpers=marker,
        semantic_validation_runtime_helpers=marker,
        semantic_post_validation_helpers=marker,
        semantic_validation_finalization_helpers=marker,
        semantic_iteration_finalization_helpers=marker,
        semantic_ac0223_runtime_helpers=marker,
        semantic_visual_override_helpers=marker,
        non_composite_runtime_helpers=marker,
        conversion_composite_helpers=marker,
        semantic_badge_runtime_helpers=marker,
        dual_arrow_badge_helpers=marker,
        dual_arrow_runtime_helpers=marker,
    )

    nested = kwargs["prepare_iteration_input_runtime_for_run_kwargs"]
    assert nested["prepare_iteration_inputs_fn"] is marker
    assert nested["extract_iteration_input_bindings_fn"] is marker
    assert nested["prepare_iteration_inputs_kwargs"]["img_path"] == "images/AC0800_L.jpg"
    assert nested["prepare_iteration_inputs_kwargs"]["csv_path"] == "descriptions.csv"
    assert kwargs["prepare_iteration_runtime_callbacks_for_run_shared_kwargs"]["run_seed"] == 1
    assert kwargs["prepare_iteration_runtime_callbacks_for_run_shared_kwargs"]["pass_seed_offset"] == 2
    assert kwargs["prepare_iteration_runtime_callbacks_for_run_impl_kwargs"]["prepare_iteration_runtime_fn"] is marker
    assert kwargs["prepare_iteration_runtime_callbacks_for_run_impl_kwargs"]["extract_iteration_runtime_bindings_fn"] is marker
    assert kwargs["prepare_iteration_runtime_callbacks_for_run_impl_kwargs"]["extract_iteration_runtime_callbacks_fn"] is marker
    assert kwargs["prepare_iteration_mode_runtime_locals_for_run_impl_kwargs"]["prepare_iteration_mode_runtime_bindings_for_run_fn"] is marker
    assert kwargs["prepare_iteration_mode_runtime_locals_for_run_impl_kwargs"]["extract_iteration_mode_runtime_locals_fn"] is marker
    assert kwargs["prepare_iteration_mode_runtime_locals_for_run_shared_kwargs"]["action_cls"] is _Action


def test_prepare_run_iteration_pipeline_locals_for_run_impl_delegates_builder_then_prepare() -> None:
    marker = object()
    calls: list[str] = []
    captured_builder_kwargs: dict[str, object] = {}
    captured_prepare_kwargs: dict[str, object] = {}

    def _build_prepare_run_kwargs_for_run(**kwargs):
        calls.append("build")
        captured_builder_kwargs.update(kwargs)
        return {"nested": "kwargs"}

    def _prepare_run_locals(**kwargs):
        calls.append("prepare")
        captured_prepare_kwargs.update(kwargs)
        return {"run": "locals"}

    original_build = helpers.buildPrepareRunIterationPipelineLocalsForRunCallKwargsImpl
    original_prepare = helpers.prepareRunIterationPipelineLocalsImpl
    helpers.buildPrepareRunIterationPipelineLocalsForRunCallKwargsImpl = _build_prepare_run_kwargs_for_run
    helpers.prepareRunIterationPipelineLocalsImpl = _prepare_run_locals
    try:
        result = helpers.prepareRunIterationPipelineLocalsForRunImpl(
            img_path="images/AC0800_L.jpg",
            csv_path="descriptions.csv",
            reports_out_dir="reports",
            svg_out_dir="svg",
            diff_out_dir="diff",
            run_seed=7,
            pass_seed_offset=3,
            action_cls=marker,
            perception_cls=marker,
            reflection_cls=marker,
            get_base_name_from_file_fn=marker,
            semantic_audit_record_fn=marker,
            semantic_quality_flags_fn=marker,
            looks_like_elongated_foreground_rect_fn=marker,
            render_embedded_raster_svg_fn=marker,
            np_module=marker,
            cv2_module=marker,
            print_fn=print,
            time_ns_fn=marker,
            iteration_run_preparation_helpers=marker,
            iteration_bindings_helpers=marker,
            iteration_initialization_helpers=marker,
            iteration_setup_helpers=marker,
            iteration_runtime_helpers=marker,
            iteration_mode_runtime_preparation_helpers=marker,
            iteration_mode_setup_helpers=marker,
            iteration_mode_preparation_helpers=marker,
            iteration_mode_dependency_setup_helpers=marker,
            iteration_mode_dependency_helpers=marker,
            iteration_mode_runtime_helpers=marker,
            iteration_orchestration_helpers=marker,
            iteration_context_helpers=marker,
            iteration_preparation_helpers=marker,
            gradient_stripe_strategy_helpers=marker,
            semantic_audit_bootstrap_helpers=marker,
            semantic_audit_logging_helpers=marker,
            semantic_audit_runtime_helpers=marker,
            semantic_mismatch_reporting_helpers=marker,
            semantic_validation_logging_helpers=marker,
            semantic_mismatch_runtime_helpers=marker,
            semantic_validation_context_helpers=marker,
            semantic_validation_runtime_helpers=marker,
            semantic_post_validation_helpers=marker,
            semantic_validation_finalization_helpers=marker,
            semantic_iteration_finalization_helpers=marker,
            semantic_ac0223_runtime_helpers=marker,
            semantic_visual_override_helpers=marker,
            non_composite_runtime_helpers=marker,
            conversion_composite_helpers=marker,
            semantic_badge_runtime_helpers=marker,
            dual_arrow_badge_helpers=marker,
            dual_arrow_runtime_helpers=marker,
        )
    finally:
        helpers.buildPrepareRunIterationPipelineLocalsForRunCallKwargsImpl = original_build
        helpers.prepareRunIterationPipelineLocalsImpl = original_prepare

    assert result == {"run": "locals"}
    assert calls == ["build", "prepare"]
    assert captured_builder_kwargs["run_seed"] == 7
    assert captured_builder_kwargs["pass_seed_offset"] == 3
    assert captured_prepare_kwargs == {"nested": "kwargs"}


def test_build_prepare_run_iteration_pipeline_locals_for_run_call_kwargs_impl_delegates() -> None:
    marker = object()
    captured_kwargs: dict[str, object] = {}

    def _build_prepare_run_kwargs_for_run(**kwargs):
        captured_kwargs.update(kwargs)
        return {"prepared": "kwargs"}

    original = helpers.buildPrepareRunIterationPipelineLocalsKwargsForRunImpl
    helpers.buildPrepareRunIterationPipelineLocalsKwargsForRunImpl = _build_prepare_run_kwargs_for_run
    try:
        result = helpers.buildPrepareRunIterationPipelineLocalsForRunCallKwargsImpl(
            img_path="images/AC0800_L.jpg",
            csv_path="descriptions.csv",
            reports_out_dir="reports",
            svg_out_dir="svg",
            diff_out_dir="diff",
            run_seed=11,
            pass_seed_offset=5,
            action_cls=marker,
            perception_cls=marker,
            reflection_cls=marker,
            get_base_name_from_file_fn=marker,
            semantic_audit_record_fn=marker,
            semantic_quality_flags_fn=marker,
            looks_like_elongated_foreground_rect_fn=marker,
            render_embedded_raster_svg_fn=marker,
            np_module=marker,
            cv2_module=marker,
            print_fn=print,
            time_ns_fn=marker,
            iteration_run_preparation_helpers=marker,
            iteration_bindings_helpers=marker,
            iteration_initialization_helpers=marker,
            iteration_setup_helpers=marker,
            iteration_runtime_helpers=marker,
            iteration_mode_runtime_preparation_helpers=marker,
            iteration_mode_setup_helpers=marker,
            iteration_mode_preparation_helpers=marker,
            iteration_mode_dependency_setup_helpers=marker,
            iteration_mode_dependency_helpers=marker,
            iteration_mode_runtime_helpers=marker,
            iteration_orchestration_helpers=marker,
            iteration_context_helpers=marker,
            iteration_preparation_helpers=marker,
            gradient_stripe_strategy_helpers=marker,
            semantic_audit_bootstrap_helpers=marker,
            semantic_audit_logging_helpers=marker,
            semantic_audit_runtime_helpers=marker,
            semantic_mismatch_reporting_helpers=marker,
            semantic_validation_logging_helpers=marker,
            semantic_mismatch_runtime_helpers=marker,
            semantic_validation_context_helpers=marker,
            semantic_validation_runtime_helpers=marker,
            semantic_post_validation_helpers=marker,
            semantic_validation_finalization_helpers=marker,
            semantic_iteration_finalization_helpers=marker,
            semantic_ac0223_runtime_helpers=marker,
            semantic_visual_override_helpers=marker,
            non_composite_runtime_helpers=marker,
            conversion_composite_helpers=marker,
            semantic_badge_runtime_helpers=marker,
            dual_arrow_badge_helpers=marker,
            dual_arrow_runtime_helpers=marker,
        )
    finally:
        helpers.buildPrepareRunIterationPipelineLocalsKwargsForRunImpl = original

    assert result == {"prepared": "kwargs"}
    assert captured_kwargs["run_seed"] == 11
    assert captured_kwargs["pass_seed_offset"] == 5
