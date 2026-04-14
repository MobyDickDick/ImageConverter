from src.iCCModules import imageCompositeConverterIterationExecution as iteration_execution_helpers


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
