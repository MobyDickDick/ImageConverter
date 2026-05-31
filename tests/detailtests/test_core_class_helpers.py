from __future__ import annotations

from src.iCCModules import imageCompositeConverterCoreClasses as core


def test_global_parameter_vector_maps_path_t_text_fields() -> None:
    params = {"cx": 1, "cy": 2, "r": 3, "text_mode": "path_t", "tx": 4, "ty": 5, "s": 0.006}

    vector = core.GlobalParameterVector.fromParams(params)
    updated = vector.applyToParams(params)

    assert vector.text_x == 4.0
    assert vector.text_y == 5.0
    assert vector.text_scale == 0.006
    assert updated["tx"] == 4.0
    assert updated["ty"] == 5.0
    assert updated["s"] == 0.006
