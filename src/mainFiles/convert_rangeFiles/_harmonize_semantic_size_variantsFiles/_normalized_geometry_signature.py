from src import image_composite_converter as _icc

globals().update(vars(_icc))

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
