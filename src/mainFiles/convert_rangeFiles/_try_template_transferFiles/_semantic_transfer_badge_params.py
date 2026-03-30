from src import image_composite_converter as _icc

globals().update(vars(_icc))

def _semantic_transfer_badge_params(
    donor_params: dict[str, object],
    target_params: dict[str, object],
    *,
    target_w: int,
    target_h: int,
    rotation_deg: int,
    scale: float,
) -> dict[str, object]:
    """Rotate/scale connector geometry around circle center while preserving upright text."""
    p = dict(donor_params)
    cx = float(p.get("cx", target_w / 2.0))
    cy = float(p.get("cy", target_h / 2.0))
    tx = float(target_params.get("cx", target_w / 2.0))
    ty = float(target_params.get("cy", target_h / 2.0))

    # Always carry essential rendering colors from target/donor/defaults.
    p["fill_gray"] = int(round(float(target_params.get("fill_gray", p.get("fill_gray", Action.LIGHT_CIRCLE_FILL_GRAY)))))
    p["stroke_gray"] = int(round(float(target_params.get("stroke_gray", p.get("stroke_gray", Action.LIGHT_CIRCLE_STROKE_GRAY)))))
    if bool(target_params.get("draw_text", p.get("draw_text", False))) or bool(p.get("draw_text", False)):
        p["text_gray"] = int(round(float(target_params.get("text_gray", p.get("text_gray", Action.LIGHT_CIRCLE_TEXT_GRAY)))))
    if bool(target_params.get("stem_enabled", p.get("stem_enabled", False))) or bool(p.get("stem_enabled", False)):
        p["stem_gray"] = int(round(float(target_params.get("stem_gray", p.get("stem_gray", p["stroke_gray"])))))

    # Prefer target anchor so center alignment remains stable between variants.
    p["cx"] = tx
    p["cy"] = ty

    if p.get("circle_enabled", True):
        p["r"] = max(1.0, float(p.get("r", 1.0)) * float(scale))

    angle = math.radians(float(rotation_deg))
    ca = math.cos(angle)
    sa = math.sin(angle)

    def _rot_scale_point(x: float, y: float) -> tuple[float, float]:
        dx = (x - cx) * float(scale)
        dy = (y - cy) * float(scale)
        rx = (dx * ca) - (dy * sa)
        ry = (dx * sa) + (dy * ca)
        return tx + rx, ty + ry

    if p.get("arm_enabled"):
        x1, y1 = _rot_scale_point(float(p.get("arm_x1", tx)), float(p.get("arm_y1", ty)))
        x2, y2 = _rot_scale_point(float(p.get("arm_x2", tx)), float(p.get("arm_y2", ty)))
        p["arm_x1"] = float(Action._clip_scalar(x1, 0.0, max(0.0, float(target_w - 1))))
        p["arm_y1"] = float(Action._clip_scalar(y1, 0.0, max(0.0, float(target_h - 1))))
        p["arm_x2"] = float(Action._clip_scalar(x2, 0.0, max(0.0, float(target_w - 1))))
        p["arm_y2"] = float(Action._clip_scalar(y2, 0.0, max(0.0, float(target_h - 1))))

    if p.get("stem_enabled"):
        stem_x = float(p.get("stem_x", tx)) + (float(p.get("stem_width", 1.0)) / 2.0)
        top = float(p.get("stem_top", ty))
        bottom = float(p.get("stem_bottom", ty))
        x1, y1 = _rot_scale_point(stem_x, top)
        x2, y2 = _rot_scale_point(stem_x, bottom)
        p["stem_x"] = float(Action._clip_scalar((x1 + x2) / 2.0 - (float(p.get("stem_width", 1.0)) / 2.0), 0.0, float(target_w)))
        p["stem_top"] = float(Action._clip_scalar(min(y1, y2), 0.0, float(target_h)))
        p["stem_bottom"] = float(Action._clip_scalar(max(y1, y2), 0.0, float(target_h)))

    # Keep text horizontally readable while preventing aggressive down-scaling
    # during template transfer. The historical sqrt(scale) shrink was often too
    # strong and produced undersized labels in converted outputs.
    if bool(p.get("draw_text", False)):
        text_scale = max(0.5, min(1.8, float(scale)))
        # Gentle response to geometric scale changes: preserve legibility for
        # downscaled transfers while still allowing moderate growth.
        text_adjust = max(0.90, min(1.18, text_scale ** 0.38))
        if "s" in p:
            p["s"] = float(max(1e-4, float(p.get("s", 0.01)) * text_adjust))
        if "co2_font_scale" in p:
            p["co2_font_scale"] = float(max(0.30, float(p.get("co2_font_scale", 0.82)) * text_adjust))
        if "voc_font_scale" in p:
            p["voc_font_scale"] = float(max(0.30, float(p.get("voc_font_scale", 0.52)) * text_adjust))

    symbol_name = str(target_params.get("label") or target_params.get("variant") or target_params.get("base") or "")
    if symbol_name:
        p = Action._finalize_ac08_style(symbol_name, p)
    return p
