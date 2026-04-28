from __future__ import annotations

from src.iCCModules import imageCompositeConverterOptimizationGlobalVector as helpers


def test_global_parameter_vector_bounds_respects_locks_by_default() -> None:
    bounds = helpers.globalParameterVectorBoundsImpl(
        {
            "cx": 10.0,
            "cy": 10.0,
            "r": 8.0,
            "lock_circle_cx": True,
            "lock_stem": True,
            "lock_text_scale": True,
        },
        30,
        50,
        circle_bounds_fn=lambda _params, _w, _h: (0.0, 29.0, 0.0, 49.0, 3.0, 12.0),
    )

    assert bounds["cx"][2] is True
    assert bounds["stem_x"][2] is True
    assert bounds["text_scale"][2] is True


def test_global_parameter_vector_bounds_unlocks_when_ac0811_unrestricted_flag_set() -> None:
    bounds = helpers.globalParameterVectorBoundsImpl(
        {
            "cx": 10.0,
            "cy": 10.0,
            "r": 8.0,
            "lock_circle_cx": True,
            "lock_stem": True,
            "lock_text_scale": True,
            "ac0811_no_restrictions": True,
        },
        30,
        50,
        circle_bounds_fn=lambda _params, _w, _h: (0.0, 29.0, 0.0, 49.0, 3.0, 12.0),
    )

    assert bounds["cx"][2] is False
    assert bounds["stem_x"][2] is False
    assert bounds["text_scale"][2] is False
    assert bounds["r"][3] == "unrestricted"
