""" End move to File mainFiles/convert_rangeFiles/_harmonize_semantic_size_variantsFiles/_read_svg_geometry.py """


""" Start move to File mainFiles/convert_rangeFiles/_harmonize_semantic_size_variantsFiles/_normalized_geometry_signature.py
import src
"""
def _normalized_geometry_signature(w: int, h: int, params: dict) -> dict[str, float]:
    sig: dict[str, float] = {}
    scale = max(1.0, float(min(w, h)))

    if params.get("circle_enabled"):
        sig["cx"] = float(params["cx"]) / max(1.0, float(w))
        sig["cy"] = float(params["cy"]) / max(1.0, float(h))
        sig["r"] = float(params["r"]) / scale
        sig["stroke_circle"] = float(params["stroke_circle"]) / scale

    if params.get("stem_enabled"):
        sig["stem_x"] = float(params["stem_x"]) / max(1.0, float(w))
        sig["stem_width"] = float(params["stem_width"]) / max(1.0, float(w))
        sig["stem_top"] = float(params["stem_top"]) / max(1.0, float(h))
        sig["stem_bottom"] = float(params["stem_bottom"]) / max(1.0, float(h))

    if params.get("arm_enabled"):
        sig["arm_x1"] = float(params["arm_x1"]) / max(1.0, float(w))
        sig["arm_y1"] = float(params["arm_y1"]) / max(1.0, float(h))
        sig["arm_x2"] = float(params["arm_x2"]) / max(1.0, float(w))
        sig["arm_y2"] = float(params["arm_y2"]) / max(1.0, float(h))
        sig["arm_stroke"] = float(params["arm_stroke"]) / scale

    return sig
""" End move to File mainFiles/convert_rangeFiles/_harmonize_semantic_size_variantsFiles/_normalized_geometry_signature.py """


""" Start move to File mainFiles/convert_rangeFiles/_harmonize_semantic_size_variantsFiles/_max_signature_delta.py
import src
"""
def _max_signature_delta(sig_a: dict[str, float], sig_b: dict[str, float]) -> float:
    keys = sorted(set(sig_a.keys()).intersection(sig_b.keys()))
    if not keys:
        return 1.0
    return max(abs(sig_a[k] - sig_b[k]) for k in keys)
""" End move to File mainFiles/convert_rangeFiles/_harmonize_semantic_size_variantsFiles/_max_signature_delta.py """


""" Start move to File mainFiles/convert_rangeFiles/_harmonize_semantic_size_variantsFiles/_scale_badge_paramsFiles/_needs_large_circle_overflow_guard.py
import src
"""
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
""" End move to File mainFiles/convert_rangeFiles/_harmonize_semantic_size_variantsFiles/_scale_badge_paramsFiles/_needs_large_circle_overflow_guard.py """


""" Start move to File mainFiles/convert_rangeFiles/_harmonize_semantic_size_variantsFiles/_scale_badge_params.py
import src
"""
