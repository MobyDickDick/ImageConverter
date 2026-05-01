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



def test_validate_badge_by_elements_stops_on_stable_non_improvement_after_fallback() -> None:
    import numpy as np
    import copy
    import math
    import os
    import time

    img = np.zeros((8, 8, 3), dtype=np.uint8)
    params = {
        "cx": 3.0,
        "cy": 3.0,
        "r": 2.0,
        "validation_stable_no_improvement_rounds": 1,
        "validation_stable_improvement_epsilon": 0.05,
    }

    logs = element_validation_helpers.validateBadgeByElementsImpl(
        img,
        params,
        max_rounds=3,
        debug_out_dir=None,
        apply_circle_geometry_penalty=True,
        stop_when_error_below_threshold=False,
        cv2_module=None,
        copy_module=copy,
        math_module=math,
        os_module=os,
        time_module=time,
        generate_badge_svg_fn=lambda *_a, **_k: "svg",
        fit_to_original_size_fn=lambda *_a, **_k: img,
        render_svg_to_numpy_fn=lambda *_a, **_k: img,
        create_diff_image_fn=lambda *_a, **_k: None,
        write_debug_image_fn=lambda *_a, **_k: None,
        element_only_params_fn=lambda p, _element: p,
        extract_badge_element_mask_fn=lambda *_a, **_k: np.ones((8, 8), dtype=np.uint8),
        element_region_mask_fn=lambda *_a, **_k: None,
        element_match_error_fn=lambda *_a, **_k: 0.0,
        refine_stem_geometry_from_masks_fn=lambda *_a, **_k: (False, None),
        optimize_element_width_bracket_fn=lambda *_a, **_k: False,
        optimize_element_extent_bracket_fn=lambda *_a, **_k: False,
        optimize_circle_center_bracket_fn=lambda *_a, **_k: False,
        optimize_circle_radius_bracket_fn=lambda *_a, **_k: False,
        optimize_global_parameter_vector_sampling_fn=lambda *_a, **_k: False,
        calculate_error_fn=lambda *_a, **_k: 25.0,
        activate_ac08_adaptive_locks_fn=lambda p, l, **_k: p.setdefault("ac08_adaptive_unlock_applied", True) or True,
        release_ac08_adaptive_locks_fn=lambda *_a, **_k: False,
        optimize_element_color_bracket_fn=lambda *_a, **_k: False,
        apply_canonical_badge_colors_fn=lambda _p: {},
    )

    assert any("stopped_due_to_stable_non_improvement" in line for line in logs)
    assert any("validation_abort_decision: stage=round_loop, reason=stable_non_improvement" in line for line in logs)
