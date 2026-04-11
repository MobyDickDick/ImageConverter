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
    valve_center_y = 25.153 * scale_y
    cx = float(params.get("cx", (float(w) / 2.0)))

    params.update(
        {
            "draw_text": False,
            "head_style": "ac0223_triple_valve",
            "head_gradient_dark": "#b2b2b3",
            "head_gradient_light": "#d9d9d9",
            "head_stroke": "#808080",
            "head_hub_fill": "#7f7f7f",
            "arm_color": "#136fad",
            "arm_x1": cx,
            "arm_x2": cx,
            "arm_y1": head_base_y,
            "arm_y2": valve_center_y,
            "head_hub_cx": cx,
            "head_hub_cy": valve_center_y,
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
    valve_center_y = 25.153 * scale_y
    cx = float(params.get("cx", defaults.get("cx", float(img.shape[1]) / 2.0)))

    default_cx = float(defaults.get("cx", cx))
    default_cy = float(defaults.get("cy", head_base_y))
    default_r = float(defaults.get("r", 0.0))
    current_cy = float(params.get("cy", default_cy))
    current_r = float(params.get("r", default_r))

    # AC0223 has a stable silhouette (circle in lower half + top valve head).
    # Tiny crops (notably *_M/*_S) can flip into a wrong local optimum where the
    # circle is detected in the upper half. In that case, fall back to defaults.
    if h > 0 and current_cy < (float(h) * 0.6):
        params["cx"] = default_cx
        params["cy"] = default_cy
        params["r"] = default_r
        cx = default_cx
        current_cy = default_cy
        current_r = default_r

    params["arm_x1"] = cx
    params["arm_x2"] = cx
    params["arm_y2"] = float(params.get("head_hub_cy", defaults.get("head_hub_cy", valve_center_y)))
    params["arm_y2"] = min(head_base_y, params["arm_y2"])
    params["arm_y1"] = max(params["arm_y2"], current_cy - current_r)
    params["draw_text"] = False
    params["head_style"] = "ac0223_triple_valve"
    params["head_gradient_dark"] = str(defaults.get("head_gradient_dark", "#b2b2b3"))
    params["head_gradient_light"] = str(defaults.get("head_gradient_light", "#d9d9d9"))
    params["head_stroke"] = str(defaults.get("head_stroke", "#808080"))
    params["head_hub_fill"] = str(defaults.get("head_hub_fill", "#7f7f7f"))
    params["arm_color"] = str(defaults.get("arm_color", "#136fad"))
    params["head_hub_cx"] = cx
    params["head_hub_cy"] = float(params["arm_y2"])
    return params
