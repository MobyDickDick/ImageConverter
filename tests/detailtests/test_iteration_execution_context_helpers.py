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
