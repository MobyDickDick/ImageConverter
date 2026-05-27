from src.iCCModules.imageCompositeConverterOptimizationFacade import (
    OptimizationHooks,
    buildDefaultOptimizationHooksImpl,
)


def test_build_default_optimization_hooks_returns_expected_bundle() -> None:
    hooks = buildDefaultOptimizationHooksImpl()
    assert isinstance(hooks, OptimizationHooks)
    assert callable(hooks.optimize_element_width_bracket_fn)
    assert callable(hooks.optimize_element_extent_bracket_fn)
    assert callable(hooks.optimize_circle_center_bracket_fn)
    assert callable(hooks.optimize_circle_radius_bracket_fn)
    assert callable(hooks.optimize_global_parameter_vector_sampling_fn)
    assert callable(hooks.optimize_element_color_bracket_fn)
