"""Extracted semantic badge fitting helpers for imageCompositeConverter."""

from __future__ import annotations

import math
from collections.abc import Callable


def stabilizeSemanticCirclePoseImpl(params: dict, defaults: dict, w: int, h: int) -> dict:
    """Bound fitted circle pose to semantic template geometry."""
    if "r" not in defaults:
        return params

    default_cx = float(defaults.get("cx", float(w) / 2.0))
    default_cy = float(defaults.get("cy", float(h) / 2.0))
    default_r = float(defaults.get("r", 0.0))
    if default_r <= 0.0:
        return params

    has_connector = bool(params.get("arm_enabled") or params.get("stem_enabled"))
    has_text = bool(params.get("draw_text", False))
    if not has_connector:
        return params

    if not has_text and min(w, h) <= 16:
        params["r"] = max(float(params.get("r", default_r)), default_r * 0.96)
        params["lock_circle_cx"] = True
        params["lock_circle_cy"] = True
        return params

    cx_tolerance = max(1.5, float(min(w, h)) * 0.18)
    cy_tolerance = max(1.5, float(min(w, h)) * 0.18)
    current_cx = float(params.get("cx", default_cx))
    current_cy = float(params.get("cy", default_cy))
    params["cx"] = float(max(default_cx - cx_tolerance, min(default_cx + cx_tolerance, current_cx)))
    params["cy"] = float(max(default_cy - cy_tolerance, min(default_cy + cy_tolerance, current_cy)))
    min_radius = max(1.0, default_r * 0.80)
    max_radius = max(min_radius, default_r * 1.45)
    current_r = float(params.get("r", default_r))
    params["r"] = float(max(min_radius, min(max_radius, current_r)))
    return params


def fitAc0870ParamsFromImageImpl(
    img,
    defaults: dict,
    *,
    cv2,
    np,
    t_xmin: int,
    t_ymax: int,
    center_glyph_bbox_fn: Callable[[dict], None],
) -> dict:
    params = dict(defaults)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape

    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    min_side = float(min(h, w))
    circles = cv2.HoughCircles(
        blurred,
        cv2.HOUGH_GRADIENT,
        dp=1.0,
        minDist=max(8.0, min_side * 0.5),
        param1=100,
        param2=10,
        minRadius=max(4, int(round(min_side * 0.25))),
        maxRadius=max(6, int(round(min_side * 0.48))),
    )

    if circles is not None and circles.size > 0:
        c = circles[0][0]
        params["cx"] = float(c[0])
        params["cy"] = float(c[1])
        params["r"] = float(c[2])

    yy, xx = np.indices(gray.shape)
    dist = np.sqrt((xx - params["cx"]) ** 2 + (yy - params["cy"]) ** 2)
    inner_mask = dist <= params["r"] * 0.88
    ring_mask = np.abs(dist - params["r"]) <= max(1.0, params["stroke_circle"])

    if np.any(inner_mask):
        inner_vals = gray[inner_mask]
        text_threshold = min(150, int(np.percentile(inner_vals, 20) + 3))
        text_mask = (gray <= text_threshold) & inner_mask

        kernel = np.ones((2, 2), np.uint8)
        text_mask_u8 = cv2.morphologyEx(text_mask.astype(np.uint8), cv2.MORPH_OPEN, kernel)
        contours, _ = cv2.findContours(text_mask_u8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if contours:
            contour = max(contours, key=cv2.contourArea)
            x, y, tw, th = cv2.boundingRect(contour)
            if tw > 2 and th > 2:
                t_width_units = 1636 - t_xmin
                t_height_units = t_ymax
                sx = tw / t_width_units
                sy = th / t_height_units
                s = float(max(0.004, min(0.04, (sx + sy) / 2.0)))
                params["s"] = s
                params["text_gray"] = int(np.median(gray[text_mask_u8 > 0]))

        center_glyph_bbox_fn(params)

        params["fill_gray"] = int(np.median(inner_vals))

    if np.any(ring_mask):
        params["stroke_gray"] = int(np.median(gray[ring_mask]))

    return params


def fitSemanticBadgeFromImageImpl(
    img,
    defaults: dict,
    *,
    cv2,
    np,
    estimate_circle_tones_and_stroke_fn: Callable[[object, float, float, float, float], tuple[float, float, float]],
    estimate_border_background_gray_fn: Callable[[object], float],
    foreground_mask_fn: Callable[[object], object],
    clip_scalar_fn: Callable[[float, float, float], float],
    center_glyph_bbox_fn: Callable[[dict], None],
    stabilize_semantic_circle_pose_fn: Callable[[dict, dict, int, int], dict],
    normalize_light_circle_colors_fn: Callable[[dict], dict],
) -> dict:
    """Fit common semantic badge primitives (circle/stem/arm) directly from image content."""
    params = dict(defaults)
    if "r" in params and "template_circle_radius" not in params:
        params["template_circle_radius"] = float(params["r"])
    if "cx" in params and "template_circle_cx" not in params:
        params["template_circle_cx"] = float(params["cx"])
    if "cy" in params and "template_circle_cy" not in params:
        params["template_circle_cy"] = float(params["cy"])
    if "stem_top" in params and "template_stem_top" not in params:
        params["template_stem_top"] = float(params["stem_top"])
    if "stem_bottom" in params and "template_stem_bottom" not in params:
        params["template_stem_bottom"] = float(params["stem_bottom"])
    if "arm_x1" in params and "template_arm_x1" not in params:
        params["template_arm_x1"] = float(params["arm_x1"])
    if "arm_y1" in params and "template_arm_y1" not in params:
        params["template_arm_y1"] = float(params["arm_y1"])
    if "arm_x2" in params and "template_arm_x2" not in params:
        params["template_arm_x2"] = float(params["arm_x2"])
    if "arm_y2" in params and "template_arm_y2" not in params:
        params["template_arm_y2"] = float(params["arm_y2"])
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape

    min_side = float(min(h, w))
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    circles = cv2.HoughCircles(
        blur,
        cv2.HOUGH_GRADIENT,
        dp=1.0,
        minDist=max(6.0, min_side * 0.35),
        param1=80,
        param2=9,
        minRadius=max(3, int(round(min_side * 0.14))),
        maxRadius=max(6, int(round(min_side * 0.60))),
    )

    if circles is not None and circles.size > 0:
        best = None
        template_cx = float(defaults.get("cx", params.get("cx", float(w) / 2.0)))
        template_cy = float(defaults.get("cy", params.get("cy", float(h) / 2.0)))
        template_r = float(defaults.get("r", params.get("r", max(1.0, min_side * 0.35))))
        max_center_offset = max(2.0, min_side * 0.42)
        max_radius_delta = max(2.0, template_r * 0.70)
        for c in circles[0]:
            cx, cy, r = float(c[0]), float(c[1]), float(c[2])
            center_offset = float(math.hypot(cx - template_cx, cy - template_cy))
            if center_offset > max_center_offset:
                continue
            yy, xx = np.indices(gray.shape)
            dist = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
            fill_mask = dist <= max(1.0, r * 0.82)
            ring_mask = np.abs(dist - r) <= max(1.0, params.get("stroke_circle", 1.2))
            if not np.any(fill_mask) or not np.any(ring_mask):
                continue
            fill_gray = float(np.median(gray[fill_mask]))
            ring_gray = float(np.median(gray[ring_mask]))
            contrast = fill_gray - ring_gray
            tone_penalty = 0.0
            if contrast < 4.0:
                tone_penalty += (4.0 - contrast) * 4.0
            if ring_gray >= fill_gray:
                tone_penalty += (ring_gray - fill_gray + 1.0) * 6.0
            score = tone_penalty
            score += (center_offset / max_center_offset) * 9.0
            score += (abs(r - template_r) / max_radius_delta) * 6.0
            if best is None or score < best[0]:
                best = (score, cx, cy, r, fill_gray, ring_gray)

        if best is not None:
            _, cx, cy, r, _fill_gray, _ring_gray = best
            params["cx"] = cx
            params["cy"] = cy
            params["r"] = r
            est_fill, est_ring, est_stroke = estimate_circle_tones_and_stroke_fn(
                gray,
                cx,
                cy,
                r,
                float(params.get("stroke_circle", defaults.get("stroke_circle", 1.2))),
            )
            params["fill_gray"] = int(round(est_fill))
            params["stroke_gray"] = int(round(est_ring))
            has_connector = bool(params.get("arm_enabled") or params.get("stem_enabled"))
            has_text = bool(params.get("draw_text", False))
            if not has_connector and not has_text:
                params["stroke_circle"] = float(max(1.0, est_stroke))
                bg_gray = estimate_border_background_gray_fn(gray)
                if bg_gray >= 240.0:
                    params["background_fill"] = "#ffffff"

    if not bool(params.get("arm_enabled") or params.get("stem_enabled")) and not bool(params.get("draw_text", False)):
        fg_mask = foreground_mask_fn(img)
        edge_touch_min = max(2, int(round(min_side * 0.20)))
        touches_all_edges = all(
            int(np.count_nonzero(edge)) >= edge_touch_min
            for edge in (fg_mask[0, :], fg_mask[-1, :], fg_mask[:, 0], fg_mask[:, -1])
        )
        if not touches_all_edges:
            bg_gray = estimate_border_background_gray_fn(gray)
            edge_dark_min = 1
            touches_all_edges = all(
                int(np.count_nonzero(edge <= (bg_gray - 6.0))) >= edge_dark_min
                for edge in (gray[0, :], gray[-1, :], gray[:, 0], gray[:, -1])
            )
        if touches_all_edges:
            border_fit_r = max(1.0, (min_side / 2.0) - 0.5)
            if float(params.get("r", 0.0)) < (border_fit_r - 0.35):
                params["cx"] = float(defaults.get("cx", float(w) / 2.0))
                params["cy"] = float(defaults.get("cy", float(h) / 2.0))
                params["r"] = float(border_fit_r)
                params["preserve_outer_diameter_on_stroke_normalization"] = True

    if "r" in defaults and "r" in params:
        default_r = float(defaults.get("r", 0.0))
        if default_r > 0.0:
            has_connector = bool(params.get("arm_enabled") or params.get("stem_enabled"))
            has_text = bool(params.get("draw_text", False))
            min_ratio = 0.80
            if not has_connector:
                min_ratio = 0.88
            if has_text and not has_connector:
                min_ratio = 0.92

            cx = float(params.get("cx", defaults.get("cx", float(w) / 2.0)))
            cy = float(params.get("cy", defaults.get("cy", float(h) / 2.0)))
            stroke = max(0.0, float(params.get("stroke_circle", defaults.get("stroke_circle", 1.0))))
            radius_limit_x = max(1.0, min(cx, float(w) - cx) - (stroke / 2.0))
            radius_limit_y = max(1.0, min(cy, float(h) - cy) - (stroke / 2.0))
            max_r = max(1.0, min(radius_limit_x, radius_limit_y))
            min_r = min(max_r, max(1.0, default_r * min_ratio))
            params["r"] = float(clip_scalar_fn(float(params.get("r", default_r)), min_r, max_r))

    if params.get("stem_enabled"):
        dark = gray <= min(225, int(np.percentile(gray, 75)))
        x1 = max(0, int(round(params["cx"] - params["r"] * 0.8)))
        x2 = min(w, int(round(params["cx"] + params["r"] * 0.8)))
        y1 = max(0, int(round(params["cy"] + params["r"] * 0.45)))
        roi = dark[y1:h, x1:x2]
        if roi.size > 0:
            cnts, _ = cv2.findContours(roi.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            best_rect = None
            for cnt in cnts:
                rx, ry, rw, rh = cv2.boundingRect(cnt)
                if rw < 1 or rh < 2 or rh <= rw:
                    continue
                area = rw * rh
                if best_rect is None or area > best_rect[0]:
                    best_rect = (area, rx, ry, rw, rh)
            if best_rect is not None:
                _, rx, ry, rw, rh = best_rect
                params["stem_x"] = float(x1 + rx)
                params["stem_top"] = float(y1 + ry)
                params["stem_width"] = float(max(1, rw))
                params["stem_bottom"] = float(min(h, y1 + ry + rh))
                stem_mask = np.zeros_like(gray, dtype=bool)
                sx1 = int(max(0, params["stem_x"]))
                sx2 = int(min(w, params["stem_x"] + params["stem_width"]))
                sy1 = int(max(0, params["stem_top"]))
                sy2 = int(min(h, params["stem_bottom"]))
                stem_mask[sy1:sy2, sx1:sx2] = True
                stem_vals = gray[stem_mask]
                if stem_vals.size > 0:
                    params["stem_gray"] = int(round(np.median(stem_vals)))

    if params.get("arm_enabled"):
        dark = gray <= min(225, int(np.percentile(gray, 75)))
        is_horizontal = abs(params.get("arm_x2", 0.0) - params.get("arm_x1", 0.0)) >= abs(
            params.get("arm_y2", 0.0) - params.get("arm_y1", 0.0)
        )
        if is_horizontal:
            side = -1 if params.get("arm_x2", 0.0) <= params.get("cx", 0.0) else 1
            y1 = max(0, int(round(params["cy"] - params["r"] * 0.6)))
            y2 = min(h, int(round(params["cy"] + params["r"] * 0.6)))
            if side < 0:
                x1 = max(0, int(round(params["cx"] - params["r"] * 2.0)))
                x2 = max(0, int(round(params["cx"] - params["r"] * 0.4)))
            else:
                x1 = min(w, int(round(params["cx"] + params["r"] * 0.4)))
                x2 = min(w, int(round(params["cx"] + params["r"] * 2.0)))
        else:
            x1 = max(0, int(round(params["cx"] - params["r"] * 0.6)))
            x2 = min(w, int(round(params["cx"] + params["r"] * 0.6)))
            y1 = max(0, int(round(params["cy"] - params["r"] * 2.0)))
            y2 = max(0, int(round(params["cy"] - params["r"] * 0.4)))

        roi = dark[y1:y2, x1:x2] if y2 > y1 and x2 > x1 else None
        if roi is not None and roi.size > 0:
            cnts, _ = cv2.findContours(roi.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            best_rect = None
            for cnt in cnts:
                rx, ry, rw, rh = cv2.boundingRect(cnt)
                if rw < 1 or rh < 1:
                    continue
                elong = (rw / max(1, rh)) if is_horizontal else (rh / max(1, rw))
                if elong < 1.2:
                    continue
                area = rw * rh
                if best_rect is None or area > best_rect[0]:
                    best_rect = (area, rx, ry, rw, rh)
            if best_rect is not None:
                _, rx, ry, rw, rh = best_rect
                if is_horizontal:
                    params["arm_x1"] = float(x1 + rx)
                    params["arm_x2"] = float(x1 + rx + rw)
                    y = float(y1 + ry + rh / 2.0)
                    params["arm_y1"] = y
                    params["arm_y2"] = y
                    params["arm_stroke"] = float(max(1.0, rh))
                else:
                    x = float(x1 + rx + rw / 2.0)
                    params["arm_x1"] = x
                    params["arm_x2"] = x
                    params["arm_y1"] = float(y1 + ry)
                    params["arm_y2"] = float(y1 + ry + rh)
                    params["arm_stroke"] = float(max(1.0, rw))

    params = stabilize_semantic_circle_pose_fn(params, defaults, w, h)

    if params.get("draw_text", True) and params.get("text_mode") in {"path", "path_t"}:
        center_glyph_bbox_fn(params)
    return normalize_light_circle_colors_fn(params)
