def _template_transfer_scale_candidates(base_scale: float) -> list[float]:
    """Build a compact scale ladder around an estimated best scale."""
    if not math.isfinite(base_scale) or base_scale <= 0.0:
        base_scale = 1.0

    multipliers = (1.00, 0.92, 1.08, 0.84, 1.18, 0.74, 1.35, 1.55)
    scales: list[float] = []
    seen: set[float] = set()
    for mul in multipliers:
        value = float(min(1.90, max(0.65, base_scale * mul)))
        key = round(value, 4)
        if key in seen:
            continue
        seen.add(key)
        scales.append(key)

    for fallback in (0.80, 0.90, 1.00, 1.10, 1.25):
        key = round(float(fallback), 4)
        if key not in seen:
            seen.add(key)
            scales.append(key)
    return scales


def _estimate_template_transfer_scale(
    img_orig: np.ndarray,
    donor_svg_text: str,
    target_w: int,
    target_h: int,
    *,
    rotation_deg: int,
) -> float | None:
    """Estimate donor->target scale from foreground silhouette bboxes."""
    rendered = Action.render_svg_to_numpy(
        _build_transformed_svg_from_template(
            donor_svg_text,
            target_w,
            target_h,
            rotation_deg=rotation_deg,
            scale=1.0,
        ),
        target_w,
        target_h,
    )
    if rendered is None:
        return None

    target_mask = Action._foreground_mask(img_orig)
    donor_mask = Action._foreground_mask(rendered)
    target_bbox = Action._mask_bbox(target_mask)
    donor_bbox = Action._mask_bbox(donor_mask)
    if target_bbox is None or donor_bbox is None:
        return None

    target_w_box = max(1e-6, float(target_bbox[2] - target_bbox[0] + 1.0))
    target_h_box = max(1e-6, float(target_bbox[3] - target_bbox[1] + 1.0))
    donor_w_box = max(1e-6, float(donor_bbox[2] - donor_bbox[0] + 1.0))
    donor_h_box = max(1e-6, float(donor_bbox[3] - donor_bbox[1] + 1.0))

    scale_w = target_w_box / donor_w_box
    scale_h = target_h_box / donor_h_box
    scale = math.sqrt(max(1e-6, scale_w * scale_h))
    if not math.isfinite(scale):
        return None
    return float(min(1.90, max(0.65, scale)))


def _template_transfer_transform_candidates(
    target_variant: str,
    donor_variant: str,
    *,
    estimated_scale_by_rotation: dict[int, float] | None = None,
) -> list[tuple[int, float]]:
    """Return ordered rotation/scale candidates for template-based fallback."""
    del target_variant, donor_variant  # reserved for future metadata-based policies

    candidates: list[tuple[int, float]] = []
    seen: set[tuple[int, float]] = set()
    for rotation in (0, 90, 180, 270):
        estimated = None
        if estimated_scale_by_rotation is not None:
            estimated = estimated_scale_by_rotation.get(rotation)
        for scale in _template_transfer_scale_candidates(estimated if estimated is not None else 1.0):
            candidate = (rotation, float(scale))
            key = (rotation, round(float(scale), 4))
            if key in seen:
                continue
            seen.add(key)
            candidates.append(candidate)
    return candidates


