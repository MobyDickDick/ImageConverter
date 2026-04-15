from src.iCCModules import imageCompositeConverterIterationRunPreparation as helpers


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
