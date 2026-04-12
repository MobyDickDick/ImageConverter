from __future__ import annotations


def finalizeAc0223BadgeParamsImpl(
    *,
    base_name: str,
    filename: str,
    width: int,
    height: int,
    badge_params: dict[str, object],
) -> dict[str, object]:
    if str(base_name).upper() != "AC0223":
        return badge_params

    scale_y = (float(height) / 75.0) if height > 0 else 1.0
    head_base_y = 39.922279 * scale_y
    hub_y = float(badge_params.get("head_hub_cy", 25.153 * scale_y))
    hub_y = max(0.0, min(head_base_y, hub_y))
    circle_top = float(badge_params.get("cy", head_base_y)) - float(badge_params.get("r", 0.0))
    badge_params["variant_name"] = str(filename).rsplit(".", 1)[0]
    badge_params["head_style"] = "ac0223_triple_valve"
    badge_params.setdefault("head_gradient_dark", "#b2b2b3")
    badge_params.setdefault("head_gradient_light", "#d9d9d9")
    badge_params.setdefault("head_stroke", "#808080")
    badge_params.setdefault("head_hub_fill", "#7f7f7f")
    badge_params.setdefault("arm_color", "#136fad")
    badge_params["arm_enabled"] = True
    badge_params.setdefault("arm_stroke", 2.0)
    badge_params["arm_x1"] = float(badge_params.get("cx", float(width) / 2.0))
    badge_params["arm_x2"] = float(badge_params.get("cx", float(width) / 2.0))
    badge_params["arm_y2"] = hub_y
    badge_params["arm_y1"] = max(hub_y, min(head_base_y, circle_top))
    badge_params["head_hub_cy"] = hub_y
    return badge_params
