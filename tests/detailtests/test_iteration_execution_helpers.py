from src.iCCModules import imageCompositeConverterIterationExecution as iteration_execution_helpers


def test_build_prepared_mode_builder_kwargs_impl_collects_runtime_fields() -> None:
    mode_runners = {"run_semantic_badge_iteration": object()}
    result = iteration_execution_helpers.buildPreparedModeBuilderKwargsImpl(
        params={"mode": "semantic_badge"},
        width=128,
        height=96,
        stripe_strategy="gradient",
        semantic_mode_visual_override=True,
        folder_path="/tmp/in",
        img_path="/tmp/in/AC0838_S.jpg",
        filename="AC0838_S.jpg",
        base_name="AC0838_S",
        description="desc",
        perc_img=[[0]],
        perc_base_name="AC0838_S",
        semantic_audit_row={"status": "semantic_pending"},
        max_iterations=9,
        badge_validation_rounds=4,
        debug_element_diff_dir="/tmp/debug/element",
        debug_ac0811_dir="/tmp/debug/ac0811",
        write_validation_log_fn=str,
        write_attempt_artifacts_fn=repr,
        record_render_failure_fn=print,
        mode_runners=mode_runners,
        calculate_error_fn=abs,
        print_fn=print,
    )

    assert result["params"] == {"mode": "semantic_badge"}
    assert result["width"] == 128
    assert result["height"] == 96
    assert result["mode_runners"] is mode_runners
    assert result["write_validation_log_fn"] is str
    assert result["write_attempt_artifacts_fn"] is repr
    assert result["record_render_failure_fn"] is print
    assert result["max_iterations"] == 9
    assert result["badge_validation_rounds"] == 4


def test_run_prepared_iteration_and_finalize_impl_builds_runs_and_finalizes() -> None:
    captured: dict[str, object] = {}

    def _build_kwargs(**kwargs):
        captured["builder_kwargs"] = kwargs
        return {"mode_runner_input": "payload"}

    def _run_mode(**kwargs):
        captured["runner_kwargs"] = kwargs
        return ("result", 0.123)

    def _finalize(**kwargs):
        captured["finalize_kwargs"] = kwargs
        return ("finalized", kwargs["mode_result"])

    result = iteration_execution_helpers.runPreparedIterationAndFinalizeImpl(
        params={"mode": "semantic_badge"},
        prepared_mode_builder_kwargs={"filename": "AC0838_S.jpg"},
        build_prepared_iteration_mode_kwargs_fn=_build_kwargs,
        run_prepared_iteration_mode_fn=_run_mode,
        finalize_iteration_result_fn=_finalize,
        math_module=__import__("math"),
    )

    assert captured["builder_kwargs"] == {"filename": "AC0838_S.jpg"}
    assert captured["runner_kwargs"] == {"mode_runner_input": "payload"}
    assert captured["finalize_kwargs"] == {
        "mode": "semantic_badge",
        "mode_result": ("result", 0.123),
        "math_module": __import__("math"),
    }
    assert result == ("finalized", ("result", 0.123))
