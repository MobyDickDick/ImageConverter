from __future__ import annotations

from src.iCCModules import imageCompositeConverterElementValidation as element_validation_helpers


def _clip_scalar(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def test_format_round_quality_progress_reports_improvement() -> None:
    message = element_validation_helpers.formatRoundQualityProgressImpl(
        120.0,
        90.0,
        start_mean_delta2=18000.0,
        end_mean_delta2=12000.0,
    )

    assert "Qualität (MAE-basiert, höher=besser): 52.94% -> 64.71%" in message
    assert "mittlere Pixelabweichung (MAE, kleiner=besser): 120.000 -> 90.000" in message
    assert "Mean-Delta² (kleiner=besser): 18000.000 -> 12000.000" in message
    assert "Qualitätsgewinn=+30.000 (+25.00%)" in message
    assert "Wirkung=verbessert" in message


def test_format_round_quality_progress_reports_stagnation_and_regression() -> None:
    unchanged = element_validation_helpers.formatRoundQualityProgressImpl(25.0, 25.0)
    worsened = element_validation_helpers.formatRoundQualityProgressImpl(80.0, 100.0)

    assert "Qualitätsgewinn=+0.000 (+0.00%)" in unchanged
    assert "Wirkung=unverändert" in unchanged
    assert "Qualitätsgewinn=-20.000 (-25.00%)" in worsened
    assert "Wirkung=verschlechtert" in worsened


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

    progress_messages: list[str] = []
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
        calculate_delta2_stats_fn=lambda *_a, **_k: (1875.0, 0.0),
        activate_ac08_adaptive_locks_fn=lambda p, l, **_k: p.setdefault("ac08_adaptive_unlock_applied", True) or True,
        release_ac08_adaptive_locks_fn=lambda *_a, **_k: False,
        optimize_element_color_bracket_fn=lambda *_a, **_k: False,
        apply_canonical_badge_colors_fn=lambda _p: {},
        progress_fn=progress_messages.append,
    )

    assert progress_messages[0].startswith(
        "[INFO] unknown: Elementvalidierung gestartet | Runden=3, Elemente=circle,text | Laufzeit="
    )
    assert any("Validierungsrunde 1/3 gestartet" in message for message in progress_messages)
    assert any("optimiere Element 'circle'" in message for message in progress_messages)
    assert any(
        "Qualität (MAE-basiert, höher=besser): 90.20% -> 90.20%" in message
        and "mittlere Pixelabweichung (MAE, kleiner=besser): 25.000 -> 25.000" in message
        and "Mean-Delta² (kleiner=besser): 1875.000 -> 1875.000" in message
        and "Wirkung=unverändert" in message
        for message in progress_messages
    )
    assert any("stopped_due_to_stable_non_improvement" in line for line in logs)
    assert any("validation_abort_decision: stage=round_loop, reason=stable_non_improvement" in line for line in logs)
    assert "best_validation_round=1" in logs
    assert "executed_validation_rounds=2" in logs
    assert "best_validation_error=25.000000" in logs


def test_action_validation_wrappers_forward_progress_callback(monkeypatch) -> None:
    import src.imageCompositeConverter as converter

    callback = object()
    captured: list[dict[str, object]] = []

    def _validate_impl(*_args, **kwargs):
        captured.append(kwargs)
        return ["ok"]

    monkeypatch.setattr(
        converter.element_validation_helpers,
        "validateBadgeByElementsImpl",
        _validate_impl,
    )

    assert converter.Action.validate_badge_by_elements(
        object(), {}, progress_fn=callback
    ) == ["ok"]
    assert captured[0]["progress_fn"] is callback
    assert callable(captured[0]["calculate_delta2_stats_fn"])
