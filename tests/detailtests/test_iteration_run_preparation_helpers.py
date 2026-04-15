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
        assert kwargs == {"mode": "kwargs"}
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
        prepare_iteration_mode_runtime_locals_for_run_kwargs_builder_fn=_build_mode_kwargs,
        prepare_iteration_mode_runtime_locals_for_run_shared_kwargs={"extra": "mode"},
    )

    assert result == {"merged": "locals"}
