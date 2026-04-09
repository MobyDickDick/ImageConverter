"""AC0223 semantic badge helper block (triple-triangle valve head + top stem)."""

from __future__ import annotations

from typing import Any, Callable


def defaultAc0223ParamsImpl(
    w: int,
    h: int,
    *,
    default_ac0813_params_fn: Callable[[int, int], dict[str, Any]],
) -> dict[str, Any]:
    """Build AC0223 defaults from AC0813 and add the valve-head style metadata."""
    params = dict(default_ac0813_params_fn(w, h))
    scale_x = (float(w) / 50.0) if w > 0 else 1.0
    scale_y = (float(h) / 75.0) if h > 0 else 1.0
    head_base_y = 39.922279 * scale_y

    params.update(
        {
            "draw_text": False,
            "head_style": "ac0223_triple_valve",
            "head_gradient_dark": "#b2b2b3",
            "head_gradient_light": "#d9d9d9",
            "head_stroke": "#808080",
            "head_hub_fill": "#7f7f7f",
            "arm_color": "#136fad",
            "arm_y1": head_base_y,
        }
    )
    return params


def fitAc0223ParamsFromImageImpl(
    img,
    defaults: dict[str, Any],
    *,
    fit_ac0813_params_from_image_fn: Callable[[Any, dict[str, Any]], dict[str, Any]],
) -> dict[str, Any]:
    """Fit AC0223 via AC0813 geometry while preserving valve-head styling."""
    params = dict(fit_ac0813_params_from_image_fn(img, defaults))
    h, _w = img.shape[:2]
    scale_y = (float(h) / 75.0) if h > 0 else 1.0
    head_base_y = 39.922279 * scale_y
    arm_y2 = float(params.get("arm_y2", defaults.get("arm_y2", head_base_y)))
    params["arm_y1"] = min(head_base_y, arm_y2)
    params["draw_text"] = False
    params["head_style"] = "ac0223_triple_valve"
    params["head_gradient_dark"] = str(defaults.get("head_gradient_dark", "#b2b2b3"))
    params["head_gradient_light"] = str(defaults.get("head_gradient_light", "#d9d9d9"))
    params["head_stroke"] = str(defaults.get("head_stroke", "#808080"))
    params["head_hub_fill"] = str(defaults.get("head_hub_fill", "#7f7f7f"))
    params["arm_color"] = str(defaults.get("arm_color", "#136fad"))
    return params
