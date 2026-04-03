"""Extracted semantic primitive detection/alignment helpers for imageCompositeConverter."""

from __future__ import annotations

import math
from collections.abc import Callable
from typing import Any


def detectSemanticPrimitivesImpl(
    img_orig: Any,
    badge_params: dict | None,
    *,
    cv2_module: Any,
    np_module: Any,
    foreground_mask_fn: Callable[[Any], Any],
    circle_from_foreground_mask_fn: Callable[[Any], tuple[float, float, float] | None],
    clip_scalar_fn: Callable[[float, float, float], float],
) -> dict[str, bool | int | str]:
    """Detect coarse semantic primitives directly from the raw bitmap."""
    h, w = img_orig.shape[:2]
    if h <= 0 or w <= 0:
        return {
            "circle": False,
            "stem": False,
            "arm": False,
            "text": False,
            "circle_detection_source": "none",
            "connector_orientation": "none",
            "horizontal_line_candidates": 0,
            "vertical_line_candidates": 0,
        }

    cv2 = cv2_module
    np = np_module
    gray = cv2.cvtColor(img_orig, cv2.COLOR_BGR2GRAY)
    fg_mask = foreground_mask_fn(img_orig).astype(np.uint8)
    min_side = max(1, min(h, w))
    badge = badge_params or {}
    small_variant = bool(badge.get("ac08_small_variant_mode", False))
    symbol_hint = str(badge.get("badge_symbol_name", "")).upper()
    circle_detection_source = "none"

    circles = cv2.HoughCircles(
        cv2.GaussianBlur(gray, (5, 5), 0),
        cv2.HOUGH_GRADIENT,
        dp=1.0,
        minDist=max(8.0, min_side * 0.30),
        param1=90,
        param2=max(8, int(round(min_side * 0.22))),
        minRadius=max(3, int(round(min_side * 0.12))),
        maxRadius=max(8, int(round(min_side * 0.48))),
    )
    has_circle = False
    circle_geom: tuple[float, float, float] | None = None
    if circles is not None and circles.size > 0:
        circle_candidates = np.round(circles[0, :]).astype(int)
        for cx, cy, radius in circle_candidates:
            r = int(max(3, radius))
            yy, xx = np.ogrid[:h, :w]
            dist = np.sqrt((xx - int(cx)) ** 2 + (yy - int(cy)) ** 2)
            ring = np.abs(dist - float(r)) <= max(1.2, float(r) * 0.20)
            if int(np.sum(ring)) <= 0:
                continue
            if float(np.mean(fg_mask[ring] > 0)) < 0.24:
                continue

            bins = 12
            coverage_bins = np.zeros(bins, dtype=np.uint8)
            for py, px in np.argwhere(ring):
                if fg_mask[py, px] <= 0:
                    continue
                ang = math.atan2(float(py - cy), float(px - cx))
                coverage_bins[int(((ang + math.pi) / (2.0 * math.pi)) * bins) % bins] = 1
            if int(np.sum(coverage_bins)) < 6:
                continue

            has_circle = True
            circle_geom = (float(cx), float(cy), float(r))
            circle_detection_source = "hough"
            break

    if not has_circle:
        fallback_circle = circle_from_foreground_mask_fn(fg_mask > 0)
        if fallback_circle is not None:
            has_circle = True
            circle_geom = fallback_circle
            circle_detection_source = "foreground_mask"

    if not has_circle and badge:
        if small_variant and symbol_hint in {"AC0811", "AC0814", "AC0870"}:
            exp_cx = float(badge.get("cx", float(w) / 2.0))
            exp_cy = float(badge.get("cy", float(h) / 2.0))
            exp_r = float(badge.get("r", max(2.0, float(min_side) * 0.28)))
            exp_r = float(clip_scalar_fn(exp_r, 2.0, float(min_side) * 0.60))
            yy, xx = np.ogrid[:h, :w]
            ring_tol = max(1.2, exp_r * 0.32)
            ring = np.abs(np.sqrt((xx - exp_cx) ** 2 + (yy - exp_cy) ** 2) - exp_r) <= ring_tol
            if int(np.count_nonzero(ring)) > 0 and float(np.mean(fg_mask[ring] > 0)) >= 0.18:
                bins = 12
                coverage_bins = np.zeros(bins, dtype=np.uint8)
                for py, px in np.argwhere(ring):
                    if fg_mask[py, px] <= 0:
                        continue
                    ang = math.atan2(float(py) - exp_cy, float(px) - exp_cx)
                    coverage_bins[int(((ang + math.pi) / (2.0 * math.pi)) * bins) % bins] = 1
                if int(np.sum(coverage_bins)) >= 5:
                    has_circle = True
                    circle_geom = (exp_cx, exp_cy, exp_r)
                    circle_detection_source = "family_fallback"

    has_arm = False
    has_stem = False
    horizontal_candidates = 0
    vertical_candidates = 0
    strongest_horizontal = 0
    strongest_vertical = 0
    lines = cv2.HoughLinesP(
        cv2.Canny(gray, 45, 140),
        rho=1,
        theta=np.pi / 180.0,
        threshold=max(8, int(round(min_side * 0.28))),
        minLineLength=max(6, int(round(float(w) * 0.22))),
        maxLineGap=max(3, int(round(min_side * 0.06))),
    )
    if lines is not None:
        for seg in lines.reshape(-1, 4):
            x1, y1, x2, y2 = [int(v) for v in seg]
            dx = abs(x2 - x1)
            dy = abs(y2 - y1)
            is_horizontal = dx >= max(6, int(round(float(w) * 0.20))) and dy <= max(1, int(round(dx * 0.18)))
            is_vertical = dy >= max(6, int(round(float(h) * 0.20))) and dx <= max(1, int(round(dy * 0.18)))
            if not is_horizontal and not is_vertical:
                continue
            if circle_geom is not None:
                cx, cy, radius = circle_geom
                endpoint_d1 = math.hypot(float(x1) - cx, float(y1) - cy)
                endpoint_d2 = math.hypot(float(x2) - cx, float(y2) - cy)
                expanded_r = float(radius) + max(1.5, float(radius) * 0.10)
                if endpoint_d1 <= expanded_r and endpoint_d2 <= expanded_r:
                    continue
                outside_len = 0.0
                if endpoint_d1 > expanded_r:
                    outside_len += max(0.0, endpoint_d1 - expanded_r)
                if endpoint_d2 > expanded_r:
                    outside_len += max(0.0, endpoint_d2 - expanded_r)
                if outside_len < max(2.0, float(w) * 0.08):
                    continue
                sample_count = max(8, max(dx, dy) + 1)
                near_ring = 0
                outside_samples = 0
                for step in range(sample_count):
                    t = step / max(1, sample_count - 1)
                    sx = float(x1) + (float(x2) - float(x1)) * t
                    sy = float(y1) + (float(y2) - float(y1)) * t
                    dist = math.hypot(sx - cx, sy - cy)
                    if dist > expanded_r:
                        outside_samples += 1
                    if abs(dist - radius) <= max(1.2, float(radius) * 0.16):
                        near_ring += 1
                if near_ring >= int(round(sample_count * 0.55)) and outside_samples <= int(round(sample_count * 0.35)):
                    continue
                if is_horizontal:
                    if abs(((float(x1) + float(x2)) / 2.0) - cx) < max(1.5, float(radius) * 0.35):
                        continue
                if is_vertical:
                    if abs(((float(y1) + float(y2)) / 2.0) - cy) < max(1.5, float(radius) * 0.35):
                        continue
            if is_horizontal:
                has_arm = True
                horizontal_candidates += 1
                strongest_horizontal = max(strongest_horizontal, dx)
            if is_vertical:
                has_stem = True
                vertical_candidates += 1
                strongest_vertical = max(strongest_vertical, dy)
            if has_arm and has_stem:
                break

    has_text = False
    x1 = max(0, int(round(float(w) * 0.15)))
    x2 = min(w, int(round(float(w) * 0.85)))
    y1 = max(0, int(round(float(h) * 0.20)))
    y2 = min(h, int(round(float(h) * 0.80)))
    roi = fg_mask[y1:y2, x1:x2]
    if roi.size > 0:
        n_labels, _labels, stats, _centroids = cv2.connectedComponentsWithStats(roi, connectivity=8)
        small_component_count = 0
        total_small_area = 0
        compact_component_count = 0
        max_small_area = max(3, int(round(float(roi.shape[0] * roi.shape[1]) * 0.12)))
        for label_idx in range(1, n_labels):
            area = int(stats[label_idx, cv2.CC_STAT_AREA])
            if not 2 <= area <= max_small_area:
                continue
            width = int(stats[label_idx, cv2.CC_STAT_WIDTH])
            height = int(stats[label_idx, cv2.CC_STAT_HEIGHT])
            aspect = float(width) / max(1.0, float(height))
            if circle_geom is not None:
                cx, cy, radius = circle_geom
                comp_cx = x1 + float(stats[label_idx, cv2.CC_STAT_LEFT] + (width / 2.0))
                comp_cy = y1 + float(stats[label_idx, cv2.CC_STAT_TOP] + (height / 2.0))
                if math.hypot(comp_cx - cx, comp_cy - cy) > float(radius) * 0.72:
                    continue
            small_component_count += 1
            total_small_area += area
            if 0.25 <= aspect <= 4.0:
                compact_component_count += 1
        has_text = (
            small_component_count >= 2
            and compact_component_count >= 2
            and total_small_area >= max(6, int(round(float(min_side) * 0.45)))
        )

    connector_orientation = "none"
    if strongest_horizontal > 0 and strongest_vertical > 0:
        shorter = min(strongest_horizontal, strongest_vertical)
        longer = max(strongest_horizontal, strongest_vertical)
        if shorter / max(1.0, float(longer)) >= 0.75:
            connector_orientation = "ambiguous"
        elif strongest_vertical > strongest_horizontal:
            connector_orientation = "vertical"
        else:
            connector_orientation = "horizontal"
    elif strongest_vertical > 0:
        connector_orientation = "vertical"
    elif strongest_horizontal > 0:
        connector_orientation = "horizontal"

    return {
        "circle": bool(has_circle),
        "stem": bool(has_stem),
        "arm": bool(has_arm),
        "text": bool(has_text),
        "circle_detection_source": circle_detection_source,
        "connector_orientation": connector_orientation,
        "horizontal_line_candidates": int(horizontal_candidates),
        "vertical_line_candidates": int(vertical_candidates),
    }


def validateSemanticDescriptionAlignmentImpl(
    img_orig: Any,
    semantic_elements: list[str],
    badge_params: dict,
    *,
    cv2_module: Any,
    np_module: Any,
    expected_presence_fn: Callable[[list[str]], dict[str, bool]],
    semantic_presence_mismatches_fn: Callable[[dict[str, bool], dict[str, bool]], list[str]],
    detect_primitives_fn: Callable[[Any, dict | None], dict[str, bool | int | str]],
    extract_mask_fn: Callable[[Any, dict, str], Any],
    mask_bbox_fn: Callable[[Any], tuple[float, float, float, float] | None],
    mask_supports_circle_fn: Callable[[Any], bool],
    foreground_mask_fn: Callable[[Any], Any],
) -> list[str]:
    cv2 = cv2_module
    np = np_module
    expected = expected_presence_fn(semantic_elements)
    expected_co2 = any("co_2" in str(elem).lower() or "co₂" in str(elem).lower() for elem in semantic_elements)
    try:
        structural = detect_primitives_fn(img_orig, badge_params)
    except TypeError:
        structural = detect_primitives_fn(img_orig)
    circle_mask = extract_mask_fn(img_orig, badge_params, "circle")
    stem_mask = extract_mask_fn(img_orig, badge_params, "stem")
    arm_mask = extract_mask_fn(img_orig, badge_params, "arm")
    text_mask = extract_mask_fn(img_orig, badge_params, "text")

    def _mask_supports_element(mask: Any, element: str) -> bool:
        if mask is None:
            return False
        pixel_count = int(np.count_nonzero(mask))
        if pixel_count < 3:
            return False
        bbox = mask_bbox_fn(mask)
        if bbox is None:
            return False
        x1, y1, x2, y2 = bbox
        width = max(1.0, (x2 - x1) + 1.0)
        height = max(1.0, (y2 - y1) + 1.0)
        density = float(pixel_count) / max(1.0, width * height)
        small_variant = bool(badge_params.get("ac08_small_variant_mode", False))
        connector_text_badge = str(badge_params.get("text_mode", "")).lower() in {"co2", "voc"}
        if element == "circle":
            if mask_supports_circle_fn(mask):
                return True
            if small_variant:
                aspect = width / max(1.0, height)
                return 0.58 <= aspect <= 1.55 and density >= 0.34 and pixel_count >= 10
            return False
        if element == "stem":
            ratio = height / max(1.0, width)
            if small_variant or connector_text_badge:
                return pixel_count >= 4 and ratio >= 1.30
            return pixel_count >= 5 and ratio >= 2.2
        if element == "arm":
            ratio = width / max(1.0, height)
            if small_variant or connector_text_badge:
                return pixel_count >= 4 and ratio >= 1.30
            return pixel_count >= 5 and ratio >= 2.2
        if element == "text":
            return pixel_count >= max(4, int(round(min(width, height) * 0.35))) and density >= 0.08
        return pixel_count >= 4

    connector_direction = str(badge_params.get("connector_family_direction", "")).lower()
    arm_is_vertical = bool(
        badge_params.get("arm_enabled", False)
        and abs(float(badge_params.get("arm_x2", 0.0)) - float(badge_params.get("arm_x1", 0.0)))
        <= abs(float(badge_params.get("arm_y2", 0.0)) - float(badge_params.get("arm_y1", 0.0)))
    )
    vertical_connector_family = bool(
        connector_direction == "vertical"
        or (
            expected.get("stem", False)
            and not expected.get("arm", False)
            and (
                (bool(badge_params.get("stem_enabled", False)) and not bool(badge_params.get("arm_enabled", False)))
                or arm_is_vertical
            )
        )
    )
    local_support = {
        "circle": _mask_supports_element(circle_mask, "circle"),
        "stem": bool(
            _mask_supports_element(stem_mask, "stem")
            or (
                vertical_connector_family
                and bool(badge_params.get("arm_enabled", False))
                and _mask_supports_element(arm_mask, "stem")
            )
        ),
        "arm": bool(not vertical_connector_family and _mask_supports_element(arm_mask, "arm")),
        "text": _mask_supports_element(text_mask, "text"),
    }
    allow_circle_mask_fallback = expected.get("circle", False) and not (
        expected.get("stem", False) or expected.get("arm", False) or expected.get("text", False)
    )
    connector_circle_mask_fallback = bool(
        expected.get("circle", False)
        and vertical_connector_family
        and local_support["circle"]
        and not local_support["arm"]
    )
    small_connector_circle_mask_fallback = bool(
        expected.get("circle", False)
        and bool(badge_params.get("ac08_small_variant_mode", False))
        and local_support["circle"]
        and (expected.get("stem", False) or expected.get("arm", False))
    )
    plain_circle_badge = bool(
        expected.get("circle", False)
        and not expected.get("stem", False)
        and not expected.get("arm", False)
        and not expected.get("text", False)
        and not bool(badge_params.get("stem_enabled", False))
        and not bool(badge_params.get("arm_enabled", False))
        and not bool(badge_params.get("draw_text", False))
    )
    require_circle_mask_confirmation = expected.get("circle", False) and not (
        allow_circle_mask_fallback or connector_circle_mask_fallback
    )
    suppress_structural_stem_for_horizontal_connector = bool(
        expected.get("arm", False)
        and not expected.get("stem", False)
        and local_support["arm"]
        and not local_support["stem"]
    )
    observed = {
        "circle": bool(
            (structural.get("circle", False) and (local_support["circle"] if require_circle_mask_confirmation else True))
            or (allow_circle_mask_fallback and local_support["circle"])
            or connector_circle_mask_fallback
            or small_connector_circle_mask_fallback
        ),
        "stem": bool(
            local_support["stem"]
            or (
                structural.get("stem", False)
                and not plain_circle_badge
                and not suppress_structural_stem_for_horizontal_connector
            )
        ),
        "arm": bool(
            local_support["arm"]
            or (
                structural.get("arm", False)
                and not structural.get("stem", False)
                and not plain_circle_badge
                and not (
                    vertical_connector_family
                    and expected.get("arm", False) is False
                    and local_support["circle"]
                    and local_support["arm"] is False
                )
            )
        ),
        "text": bool(local_support["text"] or (structural.get("text", False) and not plain_circle_badge)),
    }

    issues = semantic_presence_mismatches_fn(expected, observed)

    if expected.get("circle") and not observed["circle"]:
        issues.append("Strukturprüfung: Kein belastbarer Kreis-Kandidat im Rohbild erkannt")
    if expected.get("arm") and not observed["arm"]:
        issues.append("Strukturprüfung: Kein belastbarer waagrechter Linien-Kandidat im Rohbild erkannt")
    if expected.get("text") and not observed["text"]:
        issues.append("Strukturprüfung: Keine belastbare Textstruktur (z.B. CO₂) im Rohbild erkannt")

    if expected_co2 and expected.get("text"):
        if text_mask is None:
            issues.append("Strukturprüfung: CO₂-Textregion enthält keine verwertbaren Vordergrundpixel")
        else:
            ys, xs = np.where(text_mask)
            if ys.size == 0 or xs.size == 0:
                issues.append("Strukturprüfung: CO₂-Textregion konnte nicht lokalisiert werden")
            else:
                x1, x2 = int(xs.min()), int(xs.max())
                y1, y2 = int(ys.min()), int(ys.max())
                roi = foreground_mask_fn(img_orig)[y1 : y2 + 1, x1 : x2 + 1].astype(np.uint8)
                n_labels, _labels, stats, _centroids = cv2.connectedComponentsWithStats(roi, connectivity=8)
                compact = 0
                merged_text_blob = False
                roi_area = max(1, roi.shape[0] * roi.shape[1])
                for idx in range(1, n_labels):
                    area = int(stats[idx, cv2.CC_STAT_AREA])
                    if area < 2:
                        continue
                    width = int(stats[idx, cv2.CC_STAT_WIDTH])
                    height = int(stats[idx, cv2.CC_STAT_HEIGHT])
                    aspect = float(width) / max(1.0, float(height))
                    if 0.2 <= aspect <= 4.5:
                        compact += 1
                        density = float(area) / max(1.0, float(width * height))
                        coverage = float(area) / float(roi_area)
                        if compact == 1 and 0.75 <= aspect <= 1.80 and density >= 0.30 and coverage >= 0.18:
                            merged_text_blob = True
                if compact < 2 and not merged_text_blob:
                    issues.append("Strukturprüfung: Erwartete CO₂-Glyphenstruktur nicht ausreichend belegt")

    return issues
