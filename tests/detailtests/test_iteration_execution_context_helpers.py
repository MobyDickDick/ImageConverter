from src.iCCModules import imageCompositeConverterIterationExecutionContext as helpers


def test_build_run_prepared_iteration_and_finalize_kwargs_impl_maps_expected_keys() -> None:
    params = {"mode": "semantic_badge"}
    prepared_mode_builder_kwargs = {"base_name": "AC0831_L"}

    result = helpers.buildRunPreparedIterationAndFinalizeKwargsImpl(
        params=params,
        prepared_mode_builder_kwargs=prepared_mode_builder_kwargs,
        build_prepared_iteration_mode_kwargs_fn=object(),
        run_prepared_iteration_mode_fn=object(),
        finalize_iteration_result_fn=object(),
        math_module=object(),
    )

    assert result["params"] is params
    assert result["prepared_mode_builder_kwargs"] is prepared_mode_builder_kwargs
    assert set(result.keys()) == {
        "params",
        "prepared_mode_builder_kwargs",
        "build_prepared_iteration_mode_kwargs_fn",
        "run_prepared_iteration_mode_fn",
        "finalize_iteration_result_fn",
        "math_module",
    }


def test_build_prepared_mode_builder_kwargs_for_run_impl_maps_expected_keys() -> None:
    class _Perception:
        img = object()
        base_name = "AC0831_L"

    run_locals = {
        "params": {"mode": "semantic_badge"},
        "width": 64,
        "height": 64,
        "stripe_strategy": "none",
        "semantic_mode_visual_override": False,
        "folder_path": "/tmp/input",
        "filename": "AC0831_L.jpg",
        "base_name": "AC0831_L",
        "description": "SEMANTIC: test",
        "perception": _Perception(),
        "semantic_audit_row": {"status": "semantic_pending"},
        "write_validation_log": object(),
        "write_attempt_artifacts": object(),
        "record_render_failure": object(),
        "mode_runners": {"semantic_badge": object()},
    }

    result = helpers.buildPreparedModeBuilderKwargsForRunImpl(
        run_locals=run_locals,
        img_path="/tmp/input/AC0831_L.jpg",
        max_iterations=12,
        badge_validation_rounds=5,
        debug_element_diff_dir="/tmp/debug",
        debug_ac0811_dir="/tmp/ac0811",
        calculate_error_fn=object(),
        print_fn=print,
    )

    assert result["params"] is run_locals["params"]
    assert result["width"] == 64
    assert result["height"] == 64
    assert result["filename"] == "AC0831_L.jpg"
    assert result["base_name"] == "AC0831_L"
    assert result["perc_base_name"] == "AC0831_L"
    assert result["max_iterations"] == 12
    assert result["badge_validation_rounds"] == 5
    assert result["mode_runners"] is run_locals["mode_runners"]


def test_run_prepared_iteration_and_finalize_for_run_impl_builds_kwargs_and_runs() -> None:
    params = {"mode": "semantic_badge"}
    prepared_mode_builder_kwargs = {"base_name": "AC0831_L"}
    expected = object()

    calls: list[dict[str, object]] = []

    def _build_kwargs(**kwargs):
        calls.append(kwargs)
        return {"token": "ok"}

    def _run_prepared_iteration_and_finalize(**kwargs):
        assert kwargs == {"token": "ok"}
        return expected

    result = helpers.runPreparedIterationAndFinalizeForRunImpl(
        params=params,
        prepared_mode_builder_kwargs=prepared_mode_builder_kwargs,
        build_run_prepared_iteration_and_finalize_kwargs_fn=_build_kwargs,
        run_prepared_iteration_and_finalize_fn=_run_prepared_iteration_and_finalize,
        build_prepared_iteration_mode_kwargs_fn=object(),
        run_prepared_iteration_mode_fn=object(),
        finalize_iteration_result_fn=object(),
        math_module=object(),
    )

    assert result is expected
    assert calls and calls[0]["params"] is params
    assert calls[0]["prepared_mode_builder_kwargs"] is prepared_mode_builder_kwargs
