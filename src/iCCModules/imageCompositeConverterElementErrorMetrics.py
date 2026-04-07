from __future__ import annotations


import math


def elementOnlyParamsImpl(params: dict, element: str) -> dict:
    only = dict(params)
    only["draw_text"] = bool(params.get("draw_text", True) and element == "text")
    only["circle_enabled"] = element == "circle"
    only["stem_enabled"] = bool(params.get("stem_enabled") and element == "stem")
    only["arm_enabled"] = bool(params.get("arm_enabled") and element == "arm")
    return only


def maskedErrorImpl(img_orig, img_svg, mask, *, cv2_module, np_module) -> float:
    if img_svg is None or mask is None or int(mask.sum()) == 0:
        return float("inf")
    if img_svg.shape[:2] != img_orig.shape[:2]:
        img_svg = cv2_module.resize(img_svg, (img_orig.shape[1], img_orig.shape[0]), interpolation=cv2_module.INTER_AREA)
    gray_diff = cv2_module.cvtColor(cv2_module.absdiff(img_orig, img_svg), cv2_module.COLOR_BGR2GRAY).astype(np_module.float32)
    valid = mask.astype(np_module.float32)
    if float(np_module.sum(valid)) <= 0.0:
        return float("inf")
    weighted = gray_diff * valid
    return float(np_module.sum(weighted))


def unionBboxFromMasksImpl(mask_a, mask_b, *, mask_bbox_fn, np_module):
    boxes: list[tuple[float, float, float, float]] = []
    if mask_a is not None:
        box_a = mask_bbox_fn(mask_a)
        if box_a is not None:
            boxes.append(box_a)
    if mask_b is not None:
        box_b = mask_bbox_fn(mask_b)
        if box_b is not None:
            boxes.append(box_b)
    if not boxes:
        return None

    x1 = int(np_module.floor(min(b[0] for b in boxes)))
    y1 = int(np_module.floor(min(b[1] for b in boxes)))
    x2 = int(np_module.ceil(max(b[2] for b in boxes)))
    y2 = int(np_module.ceil(max(b[3] for b in boxes)))
    return x1, y1, x2, y2


def maskedUnionErrorInBboxImpl(
    img_orig,
    img_svg,
    mask_orig,
    mask_svg,
    *,
    cv2_module,
    np_module,
    union_bbox_from_masks_fn,
) -> float:
    """Symmetric masked error, cropped to the smallest rectangle around both masks."""
    if img_svg is None or mask_orig is None or mask_svg is None:
        return float("inf")
    if not hasattr(img_orig, "__getitem__"):
        return 0.0
    if img_svg.shape[:2] != img_orig.shape[:2]:
        img_svg = cv2_module.resize(img_svg, (img_orig.shape[1], img_orig.shape[0]), interpolation=cv2_module.INTER_AREA)

    bbox = union_bbox_from_masks_fn(mask_orig, mask_svg)
    if bbox is None:
        return float("inf")

    h, w = img_orig.shape[:2]
    x1, y1, x2, y2 = bbox
    x1 = max(0, min(w - 1, x1))
    y1 = max(0, min(h - 1, y1))
    x2 = max(x1, min(w - 1, x2))
    y2 = max(y1, min(h - 1, y2))

    orig_crop = img_orig[y1 : y2 + 1, x1 : x2 + 1]
    svg_crop = img_svg[y1 : y2 + 1, x1 : x2 + 1]
    union_mask = mask_orig[y1 : y2 + 1, x1 : x2 + 1] | mask_svg[y1 : y2 + 1, x1 : x2 + 1]
    if int(np_module.sum(union_mask)) <= 0:
        return float("inf")

    gray_diff = cv2_module.cvtColor(cv2_module.absdiff(orig_crop, svg_crop), cv2_module.COLOR_BGR2GRAY).astype(np_module.float32)
    return float(np_module.sum(gray_diff * union_mask.astype(np_module.float32)))


def elementMatchErrorImpl(
    img_orig,
    img_svg,
    params: dict,
    element: str,
    *,
    mask_orig=None,
    mask_svg=None,
    apply_circle_geometry_penalty: bool = True,
    cv2_module,
    np_module,
    math_module,
    extract_badge_element_mask_fn,
    masked_union_error_in_bbox_fn,
    mask_centroid_radius_fn,
) -> float:
    """Element score for optimization: localization + redraw + symmetric compare."""
    if img_svg is None:
        return float("inf")
    if img_svg.shape[:2] != img_orig.shape[:2]:
        img_svg = cv2_module.resize(img_svg, (img_orig.shape[1], img_orig.shape[0]), interpolation=cv2_module.INTER_AREA)

    local_mask_orig = mask_orig if mask_orig is not None else extract_badge_element_mask_fn(img_orig, params, element)
    local_mask_svg = mask_svg if mask_svg is not None else extract_badge_element_mask_fn(img_svg, params, element)
    if local_mask_orig is None or local_mask_svg is None:
        return float("inf")

    orig_area = float(np_module.sum(local_mask_orig))
    svg_area = float(np_module.sum(local_mask_svg))
    if orig_area <= 0.0 or svg_area <= 0.0:
        return float("inf")

    photo_err = float(masked_union_error_in_bbox_fn(img_orig, img_svg, local_mask_orig, local_mask_svg))
    if not math_module.isfinite(photo_err):
        return float("inf")

    inter = float(np_module.sum(local_mask_orig & local_mask_svg))
    union = float(np_module.sum(local_mask_orig | local_mask_svg))
    if union <= 0.0:
        return float("inf")

    miss = float(np_module.sum(local_mask_orig & (~local_mask_svg))) / orig_area
    extra = float(np_module.sum(local_mask_svg & (~local_mask_orig))) / orig_area
    if bool(params.get("ac08_small_variant_mode", False)):
        aa_bias = float(max(0.0, params.get("small_variant_antialias_bias", 0.0)))
        miss = max(0.0, miss - aa_bias)
        extra = max(0.0, extra - (aa_bias * 0.75))
    iou = inter / union

    photo_norm = photo_err / max(1.0, orig_area)

    if element == "circle" and apply_circle_geometry_penalty:
        src_circle = mask_centroid_radius_fn(local_mask_orig)
        cand_circle = mask_centroid_radius_fn(local_mask_svg)
        if src_circle is not None and cand_circle is not None:
            src_cx, src_cy, src_r = src_circle
            cand_cx, cand_cy, cand_r = cand_circle
            center_dist = float(math_module.hypot(cand_cx - src_cx, cand_cy - src_cy))
            center_norm = center_dist / max(1.0, src_r)
            undersize_ratio = max(0.0, (src_r - cand_r) / max(1.0, src_r))
            extra += undersize_ratio * 0.35
            miss += undersize_ratio * 0.45
            iou = max(0.0, iou - min(0.35, undersize_ratio * 0.55))
            photo_norm += center_norm * 2.8

    return float(photo_norm + (38.0 * miss) + (24.0 * extra) + (18.0 * (1.0 - iou)))


def calculateDelta2StatsImpl(img_orig, img_svg, *, cv2_module, np_module) -> tuple[float, float]:
    """Return mean/std of per-pixel squared RGB deltas."""
    if img_svg is None:
        return float("inf"), float("inf")
    if img_svg.shape[:2] != img_orig.shape[:2]:
        img_svg = cv2_module.resize(
            img_svg,
            (img_orig.shape[1], img_orig.shape[0]),
            interpolation=cv2_module.INTER_AREA,
        )
    diff = img_orig.astype(np_module.float32) - img_svg.astype(np_module.float32)
    delta2 = np_module.sum(diff * diff, axis=2)
    return float(np_module.mean(delta2)), float(np_module.std(delta2))

