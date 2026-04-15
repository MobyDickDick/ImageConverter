from src.iCCModules import imageCompositeConverterIterationBindings as helpers


def test_extract_iteration_input_runtime_fields_impl_maps_expected_keys() -> None:
    source = {
        "folder_path": "images",
        "filename": "AC0811_M.jpg",
        "perception": object(),
        "width": 128,
        "height": 64,
        "description": "desc",
        "params": {"mode": "semantic_badge"},
        "stripe_strategy": "none",
        "semantic_audit_row": {"status": "pending"},
        "unused": "value",
    }

    result = helpers.extractIterationInputRuntimeFieldsImpl(
        iteration_input_bindings=source,
    )

    assert set(result.keys()) == {
        "folder_path",
        "filename",
        "perception",
        "width",
        "height",
        "description",
        "params",
        "stripe_strategy",
        "semantic_audit_row",
    }
    assert result["filename"] == "AC0811_M.jpg"


def test_extract_iteration_runtime_callbacks_impl_maps_expected_keys() -> None:
    source = {
        "base_name": "AC0811_M",
        "write_validation_log": lambda *_args, **_kwargs: None,
        "write_attempt_artifacts": lambda *_args, **_kwargs: None,
        "record_render_failure": lambda *_args, **_kwargs: None,
        "unused": "value",
    }

    result = helpers.extractIterationRuntimeCallbacksImpl(
        iteration_runtime_bindings=source,
    )

    assert set(result.keys()) == {
        "base_name",
        "write_validation_log",
        "write_attempt_artifacts",
        "record_render_failure",
    }
    assert result["base_name"] == "AC0811_M"


def test_extract_iteration_input_runtime_locals_impl_maps_expected_keys() -> None:
    source = {
        "folder_path": "images",
        "filename": "AC0831_L.jpg",
        "perception": object(),
        "width": 96,
        "height": 96,
        "description": "desc",
        "params": {"mode": "semantic_badge"},
        "stripe_strategy": "auto",
        "semantic_audit_row": {"status": "semantic_pending"},
        "unused": "value",
    }

    result = helpers.extractIterationInputRuntimeLocalsImpl(
        iteration_input_runtime_fields=source,
    )

    assert set(result.keys()) == {
        "folder_path",
        "filename",
        "perception",
        "width",
        "height",
        "description",
        "params",
        "stripe_strategy",
        "semantic_audit_row",
    }
    assert result["filename"] == "AC0831_L.jpg"


def test_extract_iteration_runtime_callback_locals_impl_maps_expected_keys() -> None:
    source = {
        "base_name": "AC0831_L",
        "write_validation_log": lambda *_args, **_kwargs: None,
        "write_attempt_artifacts": lambda *_args, **_kwargs: None,
        "record_render_failure": lambda *_args, **_kwargs: None,
        "unused": "value",
    }

    result = helpers.extractIterationRuntimeCallbackLocalsImpl(
        iteration_runtime_callbacks=source,
    )

    assert set(result.keys()) == {
        "base_name",
        "write_validation_log",
        "write_attempt_artifacts",
        "record_render_failure",
    }
    assert result["base_name"] == "AC0831_L"


def test_extract_iteration_mode_runtime_bindings_impl_maps_expected_keys() -> None:
    source = {
        "params": {"mode": "semantic_badge"},
        "semantic_mode_visual_override": True,
        "mode_runners": {"semantic_badge": object()},
        "unused": "value",
    }

    result = helpers.extractIterationModeRuntimeBindingsImpl(
        iteration_mode_runtime_bindings=source,
    )

    assert set(result.keys()) == {
        "params",
        "semantic_mode_visual_override",
        "mode_runners",
    }
    assert result["semantic_mode_visual_override"] is True


def test_extract_iteration_mode_runtime_locals_impl_maps_expected_keys() -> None:
    source = {
        "params": {"mode": "semantic_badge"},
        "semantic_mode_visual_override": False,
        "mode_runners": {"semantic_badge": object()},
        "unused": "value",
    }

    result = helpers.extractIterationModeRuntimeLocalsImpl(
        iteration_mode_runtime_fields=source,
    )

    assert set(result.keys()) == {
        "params",
        "semantic_mode_visual_override",
        "mode_runners",
    }
    assert result["semantic_mode_visual_override"] is False


def test_extract_run_iteration_pipeline_locals_impl_maps_expected_keys() -> None:
    input_runtime = {
        "folder_path": "images",
        "filename": "AC0800_L.jpg",
        "perception": object(),
        "width": 120,
        "height": 80,
        "description": "desc",
        "params": {"mode": "composite"},
        "stripe_strategy": "none",
        "semantic_audit_row": {"status": "semantic_pending"},
    }
    runtime_callbacks = {
        "base_name": "AC0800_L",
        "write_validation_log": lambda *_args, **_kwargs: None,
        "write_attempt_artifacts": lambda *_args, **_kwargs: None,
        "record_render_failure": lambda *_args, **_kwargs: None,
    }
    mode_runtime = {
        "params": {"mode": "semantic_badge"},
        "semantic_mode_visual_override": True,
        "mode_runners": {"semantic_badge": object()},
    }

    result = helpers.extractRunIterationPipelineLocalsImpl(
        iteration_input_runtime_locals=input_runtime,
        iteration_runtime_callback_locals=runtime_callbacks,
        iteration_mode_runtime_locals=mode_runtime,
    )

    assert set(result.keys()) == {
        "folder_path",
        "filename",
        "perception",
        "width",
        "height",
        "description",
        "params",
        "stripe_strategy",
        "semantic_audit_row",
        "base_name",
        "write_validation_log",
        "write_attempt_artifacts",
        "record_render_failure",
        "semantic_mode_visual_override",
        "mode_runners",
    }
    assert result["params"] == {"mode": "semantic_badge"}
