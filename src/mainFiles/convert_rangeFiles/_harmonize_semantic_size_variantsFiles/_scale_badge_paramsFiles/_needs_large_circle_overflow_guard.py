from src import image_composite_converter as _icc

globals().update(vars(_icc))

def _needs_large_circle_overflow_guard(params: dict) -> bool:
    """Return whether circle placement may intentionally exceed canvas bounds.

    This is a generic geometry rule for large, centered CO² badges without
    connectors. It replaces single-variant checks (for example ``AC0820_L``)
    so future families with the same structure automatically get the same
    robust radius handling.
    """
    if not bool(params.get("circle_enabled", True)):
        return False
    if bool(params.get("arm_enabled") or params.get("stem_enabled")):
        return False
    if not bool(params.get("draw_text", False)):
        return False
    if str(params.get("text_mode", "")).lower() != "co2":
        return False

    template_r = float(params.get("template_circle_radius", params.get("r", 0.0)) or 0.0)
    current_r = float(params.get("r", 0.0) or 0.0)
    width = float(params.get("width", params.get("badge_width", 0.0)) or 0.0)

    large_template = template_r >= 10.0
    large_current = current_r >= 10.0
    wide_canvas = width >= 30.0
    return bool(large_template or large_current or wide_canvas)
