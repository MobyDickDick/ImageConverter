from __future__ import annotations

from src.iCCModules import imageCompositeConverterOptimizationGlobalVector as helpers


def test_global_parameter_vector_bounds_use_path_t_scale_domain() -> None:
    bounds = helpers.globalParameterVectorBoundsImpl(
        {"cx": 5.0, "cy": 5.0, "r": 4.0, "text_mode": "path_t", "s": 0.006},
        15,
        15,
        circle_bounds_fn=lambda _params, _w, _h: (0.0, 14.0, 0.0, 14.0, 1.0, 7.0),
    )

    low, high, locked, source = bounds["text_scale"]
    assert low == 0.003
    assert high == 0.0108
    assert locked is False
    assert source == "semantic"
