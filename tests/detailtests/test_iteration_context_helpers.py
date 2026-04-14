from src.iCCModules import imageCompositeConverterIterationContext as helpers


def test_extract_iteration_input_bindings_impl_maps_prepare_output_keys():
    inputs = {
        "folder_path": "/tmp/in",
        "filename": "AC0838_S.jpg",
        "perception": object(),
        "width": 80,
        "height": 64,
        "description": "desc",
        "params": {"mode": "semantic_badge"},
        "stripe_strategy": "foreground",
        "semantic_audit_row": {"status": "semantic_pending"},
    }

    result = helpers.extractIterationInputBindingsImpl(iteration_inputs=inputs)

    assert result["folder_path"] == "/tmp/in"
    assert result["filename"] == "AC0838_S.jpg"
    assert result["perception"] is inputs["perception"]
    assert result["width"] == 80
    assert result["height"] == 64
    assert result["description"] == "desc"
    assert result["params"] == {"mode": "semantic_badge"}
    assert result["stripe_strategy"] == "foreground"
    assert result["semantic_audit_row"] == {"status": "semantic_pending"}


def test_extract_iteration_mode_runtime_bindings_impl_exposes_mode_runtime_fields():
    mode_runtime = {
        "params": {"mode": "non_composite"},
        "semantic_mode_visual_override": True,
        "mode_runners": {"run_non_composite_iteration": object()},
    }

    result = helpers.extractIterationModeRuntimeBindingsImpl(mode_runtime=mode_runtime)

    assert result["params"] is mode_runtime["params"]
    assert result["semantic_mode_visual_override"] is True
    assert result["mode_runners"] is mode_runtime["mode_runners"]


def test_build_prepared_iteration_mode_kwargs_impl_maps_mode_runners_and_callbacks():
    callbacks = {
        "write_validation_log": lambda *_args, **_kwargs: None,
        "write_attempt_artifacts": lambda *_args, **_kwargs: None,
        "record_render_failure": lambda *_args, **_kwargs: None,
    }
    mode_runners = {
        "run_semantic_badge_iteration": object(),
        "run_dual_arrow_badge_iteration": object(),
        "run_non_composite_iteration": object(),
        "run_composite_iteration": object(),
    }

    result = helpers.buildPreparedIterationModeKwargsImpl(
        params={"mode": "semantic_badge", "x": 1},
        width=64,
        height=48,
        stripe_strategy="gradient",
        semantic_mode_visual_override=True,
        folder_path="/tmp/in",
        img_path="/tmp/in/AC0800_S.jpg",
        filename="AC0800_S.jpg",
        base_name="AC0800_S",
        description="desc",
        perc_img=[[0]],
        perc_base_name="AC0800_S",
        semantic_audit_row={"status": "semantic_pending"},
        max_iterations=7,
        badge_validation_rounds=3,
        debug_element_diff_dir="/tmp/debug/element",
        debug_ac0811_dir="/tmp/debug/ac0811",
        write_validation_log_fn=callbacks["write_validation_log"],
        write_attempt_artifacts_fn=callbacks["write_attempt_artifacts"],
        record_render_failure_fn=callbacks["record_render_failure"],
        mode_runners=mode_runners,
        calculate_error_fn=abs,
        print_fn=print,
    )

    assert result["mode"] == "semantic_badge"
    assert result["run_semantic_badge_iteration_fn"] is mode_runners["run_semantic_badge_iteration"]
    assert result["run_dual_arrow_badge_iteration_fn"] is mode_runners["run_dual_arrow_badge_iteration"]
    assert result["run_non_composite_iteration_fn"] is mode_runners["run_non_composite_iteration"]
    assert result["run_composite_iteration_fn"] is mode_runners["run_composite_iteration"]
    assert result["write_validation_log_fn"] is callbacks["write_validation_log"]
    assert result["write_attempt_artifacts_fn"] is callbacks["write_attempt_artifacts"]
    assert result["record_render_failure_fn"] is callbacks["record_render_failure"]
    assert result["max_iterations"] == 7
    assert result["badge_validation_rounds"] == 3
