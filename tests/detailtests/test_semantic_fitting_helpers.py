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

    assert float(stabilized["cx"]) == 10.5
    assert float(stabilized["cy"]) == 24.0
    assert float(stabilized["r"]) >= 8.8
