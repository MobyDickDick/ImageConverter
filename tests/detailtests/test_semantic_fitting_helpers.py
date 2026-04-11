from __future__ import annotations

from src.iCCModules import imageCompositeConverterSemanticFitting as fitting_helpers


def test_stabilize_semantic_circle_pose_keeps_vertical_connector_text_close_to_template() -> None:
    defaults = {
        "cx": 10.0,
        "cy": 25.0,
        "r": 9.5,
        "stroke_circle": 1.0,
    }
    params = {
        "arm_enabled": True,
        "draw_text": True,
        "arm_x1": 10.0,
        "arm_x2": 10.0,
        "cx": 12.0,
        "cy": 22.0,
        "r": 6.0,
        "stroke_circle": 1.0,
    }

    stabilized = fitting_helpers.stabilizeSemanticCirclePoseImpl(params, defaults, w=20, h=35)

    assert float(stabilized["cx"]) == 10.6
    assert float(stabilized["cy"]) == 23.8
    assert float(stabilized["r"]) >= 8.8


def test_enforce_directional_circle_side_resets_vertical_badge_when_circle_flips_up() -> None:
    defaults = {
        "cx": 15.0,
        "cy": 30.0,
        "r": 12.0,
        "arm_enabled": True,
        "arm_x1": 15.0,
        "arm_y1": 0.0,
        "arm_x2": 15.0,
        "arm_y2": 18.0,
    }
    params = {"arm_enabled": True, "cx": 14.0, "cy": 12.0, "r": 10.0}

    corrected = fitting_helpers.enforceDirectionalCircleSideImpl(params, defaults, w=30, h=45)

    assert float(corrected["cx"]) == 15.0
    assert float(corrected["cy"]) == 30.0
    assert float(corrected["r"]) >= 11.04
