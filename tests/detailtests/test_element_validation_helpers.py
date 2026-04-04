from __future__ import annotations

from src.iCCModules import imageCompositeConverterElementValidation as element_validation_helpers


def _clip_scalar(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def test_apply_element_alignment_step_updates_circle_geometry() -> None:
    params = {"cx": 20.0, "cy": 20.0, "r": 10.0}

    changed = element_validation_helpers.applyElementAlignmentStepImpl(
        params,
        "circle",
        center_dx=4.0,
        center_dy=-2.0,
        diag_scale=1.1,
        w=100,
        h=100,
        clip_scalar_fn=_clip_scalar,
    )

    assert changed is True
    assert params["cx"] > 20.0
    assert params["cy"] < 20.0
    assert params["r"] > 10.0


def test_apply_element_alignment_step_honors_locked_circle_center() -> None:
    params = {
        "cx": 30.0,
        "cy": 30.0,
        "r": 12.0,
        "lock_circle_cx": True,
        "lock_circle_cy": True,
    }

    element_validation_helpers.applyElementAlignmentStepImpl(
        params,
        "circle",
        center_dx=10.0,
        center_dy=10.0,
        diag_scale=1.05,
        w=100,
        h=100,
        clip_scalar_fn=_clip_scalar,
    )

    assert params["cx"] == 30.0
    assert params["cy"] == 30.0

