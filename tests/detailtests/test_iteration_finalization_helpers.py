from src.iCCModules import imageCompositeConverterIterationFinalization as iteration_finalization_helpers


def test_finalize_iteration_result_impl_returns_non_composite_result_unchanged() -> None:
    mode_result = ("AC0838_S", "desc", {"mode": "semantic_badge"}, 3, 0.42)

    result = iteration_finalization_helpers.finalizeIterationResultImpl(
        mode="semantic_badge",
        mode_result=mode_result,
        math_module=__import__("math"),
    )

    assert result is mode_result


def test_finalize_iteration_result_impl_drops_non_finite_composite_error() -> None:
    mode_result = ("AC0800_S", "desc", {"mode": "composite"}, 5, float("inf"))

    result = iteration_finalization_helpers.finalizeIterationResultImpl(
        mode="composite",
        mode_result=mode_result,
        math_module=__import__("math"),
    )

    assert result is None


def test_finalize_iteration_result_impl_accepts_short_composite_tuple_shape() -> None:
    mode_result = (7, 0.125)

    result = iteration_finalization_helpers.finalizeIterationResultImpl(
        mode="composite",
        mode_result=mode_result,
        math_module=__import__("math"),
    )

    assert result is mode_result
