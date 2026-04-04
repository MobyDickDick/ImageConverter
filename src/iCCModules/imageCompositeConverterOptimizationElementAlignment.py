"""Extracted element-alignment optimization helpers for imageCompositeConverter."""

from __future__ import annotations

def applyElementAlignmentStepImpl(
    params: dict,
    element: str,
    center_dx: float,
    center_dy: float,
    diag_scale: float,
    w: int,
    h: int,
    *,
    clip_scalar_fn,
    apply_circle_geometry_penalty: bool = True,
) -> bool:
    changed = False
    scale = float(clip_scalar_fn(diag_scale, 0.85, 1.18))

    if element == "circle" and apply_circle_geometry_penalty:
        old_cx = float(params["cx"])
        old_cy = float(params["cy"])
        old_r = float(params["r"])
        min_r = float(max(1.0, params.get("min_circle_radius", 1.0)))
        if "circle_radius_lower_bound_px" in params:
            min_r = float(max(min_r, float(params.get("circle_radius_lower_bound_px", min_r))))
        max_r = float(min(w, h)) * 0.48
        if bool(params.get("allow_circle_overflow", False)):
            max_r = max(max_r, float(max(w, h)) * 1.25, min_r + 0.5)
        if bool(params.get("lock_circle_cx", False)):
            params["cx"] = old_cx
        else:
            params["cx"] = float(clip_scalar_fn(old_cx + center_dx * 0.65, 0.0, float(w - 1)))
        if bool(params.get("lock_circle_cy", False)):
            params["cy"] = old_cy
        else:
            params["cy"] = float(clip_scalar_fn(old_cy + center_dy * 0.65, 0.0, float(h - 1)))
        params["r"] = float(clip_scalar_fn(old_r * scale, min_r, max_r))
        changed = (
            abs(params["cx"] - old_cx) > 0.02
            or abs(params["cy"] - old_cy) > 0.02
            or abs(params["r"] - old_r) > 0.02
        )

    elif element == "stem" and params.get("stem_enabled"):
        old_x = float(params["stem_x"])
        old_w = float(params["stem_width"])
        old_top = float(params["stem_top"])
        old_bottom = float(params["stem_bottom"])

        stem_cx = old_x + (old_w / 2.0)
        if bool(params.get("lock_stem_center_to_circle", False)):
            stem_cx = float(params.get("cx", stem_cx))
        else:
            stem_cx = float(clip_scalar_fn(stem_cx + center_dx * 0.75, 0.0, float(w - 1)))
        new_w = float(clip_scalar_fn(old_w * scale, 1.0, float(w) * 0.22))
        params["stem_width"] = new_w
        params["stem_x"] = float(clip_scalar_fn(stem_cx - (new_w / 2.0), 0.0, float(w) - new_w))
        params["stem_top"] = float(clip_scalar_fn(old_top + center_dy * 0.45, 0.0, float(h - 2)))
        params["stem_bottom"] = float(clip_scalar_fn(old_bottom + center_dy * 0.25, params["stem_top"] + 1.0, float(h - 1)))
        changed = (
            abs(params["stem_x"] - old_x) > 0.02
            or abs(params["stem_width"] - old_w) > 0.02
            or abs(params["stem_top"] - old_top) > 0.02
            or abs(params["stem_bottom"] - old_bottom) > 0.02
        )

    elif element == "arm" and params.get("arm_enabled"):
        old_x1 = float(params["arm_x1"])
        old_x2 = float(params["arm_x2"])
        old_y1 = float(params["arm_y1"])
        old_y2 = float(params["arm_y2"])
        old_stroke = float(params.get("arm_stroke", params.get("stem_or_arm", 1.0)))

        ax1 = old_x1 + center_dx * 0.75
        ax2 = old_x2 + center_dx * 0.75
        ay1 = old_y1 + center_dy * 0.75
        ay2 = old_y2 + center_dy * 0.75
        acx = (ax1 + ax2) / 2.0
        acy = (ay1 + ay2) / 2.0
        vx = (ax2 - ax1) * scale
        vy = (ay2 - ay1) * scale

        params["arm_x1"] = float(clip_scalar_fn(acx - (vx / 2.0), 0.0, float(w - 1)))
        params["arm_x2"] = float(clip_scalar_fn(acx + (vx / 2.0), 0.0, float(w - 1)))
        params["arm_y1"] = float(clip_scalar_fn(acy - (vy / 2.0), 0.0, float(h - 1)))
        params["arm_y2"] = float(clip_scalar_fn(acy + (vy / 2.0), 0.0, float(h - 1)))
        params["arm_stroke"] = float(clip_scalar_fn(old_stroke * scale, 1.0, float(min(w, h)) * 0.18))
        changed = (
            abs(params["arm_x1"] - old_x1) > 0.02
            or abs(params["arm_x2"] - old_x2) > 0.02
            or abs(params["arm_y1"] - old_y1) > 0.02
            or abs(params["arm_y2"] - old_y2) > 0.02
            or abs(params["arm_stroke"] - old_stroke) > 0.02
        )

    elif element == "text" and params.get("draw_text", True):
        mode = str(params.get("text_mode", "")).lower()
        r = max(1.0, float(params.get("r", min(w, h) * 0.45)))
        if mode == "co2":
            old_dy = float(params.get("co2_dy", 0.0))
            params["co2_dy"] = float(clip_scalar_fn(old_dy + center_dy * 0.75, -0.45 * r, 0.45 * r))
            changed = abs(params["co2_dy"] - old_dy) > 0.02
        elif mode == "voc":
            old_dy = float(params.get("voc_dy", 0.0))
            params["voc_dy"] = float(clip_scalar_fn(old_dy + center_dy * 0.75, -0.45 * r, 0.45 * r))
            changed = abs(params["voc_dy"] - old_dy) > 0.02
        elif "ty" in params:
            old_ty = float(params.get("ty", 0.0))
            params["ty"] = float(clip_scalar_fn(old_ty + center_dy * 0.75, 0.0, float(h - 1)))
            changed = abs(params["ty"] - old_ty) > 0.02

    return changed


def estimateVerticalStemFromMaskImpl(
    mask,
    expected_cx: float,
    y_start: int,
    y_end: int,
    *,
    np_module,
) -> tuple[float, float] | None:
    """Estimate stem center/width from foreground mask rows."""
    h, w = mask.shape[:2]
    y1 = max(0, min(h, int(y_start)))
    y2 = max(y1, min(h, int(y_end)))
    if y2 <= y1:
        return None

    span = y2 - y1
    if span >= 8:
        y1 = min(y2 - 1, y1 + int(round(span * 0.25)))

    widths: list[float] = []
    centers: list[float] = []
    cx_idx = int(round(expected_cx))
    for y in range(y1, y2):
        row = mask[y]
        xs = np_module.where(row)[0]
        if xs.size == 0:
            continue
        split_points = np_module.where(np_module.diff(xs) > 1)[0]
        runs = np_module.split(xs, split_points + 1)
        if not runs:
            continue
        chosen = None
        nearest_dist = float("inf")
        for run in runs:
            rx1, rx2 = int(run[0]), int(run[-1])
            if rx1 <= cx_idx <= rx2:
                chosen = run
                break
            dist = min(abs(cx_idx - rx1), abs(cx_idx - rx2))
            if dist < nearest_dist:
                nearest_dist = dist
                chosen = run
        if chosen is None:
            continue
        widths.append(float((chosen[-1] - chosen[0]) + 1))
        centers.append(float((chosen[0] + chosen[-1]) / 2.0))

    if not widths:
        return None

    widths_arr = np_module.array(widths, dtype=np_module.float32)
    centers_arr = np_module.array(centers, dtype=np_module.float32)
    keep = np_module.ones(widths_arr.shape[0], dtype=bool)
    for _ in range(3):
        sel_w = widths_arr[keep]
        if sel_w.size < 3:
            break
        med = float(np_module.median(sel_w))
        tol = max(1.0, med * 0.35)
        new_keep = keep & (np_module.abs(widths_arr - med) <= tol)
        if int(np_module.sum(new_keep)) == int(np_module.sum(keep)):
            break
        keep = new_keep

    if int(np_module.sum(keep)) == 0:
        return None

    est_width = float(np_module.median(widths_arr[keep]))
    est_cx = float(np_module.median(centers_arr[keep]))
    est_width = max(1.0, min(est_width, float(w)))
    return est_cx, est_width
