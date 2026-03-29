    template transfers.
    """

    prev_error_pp = float(old_row.get("error_per_pixel", float("inf")))
    new_error_pp = float(new_row.get("error_per_pixel", float("inf")))
    prev_mean_delta2 = float(old_row.get("mean_delta2", float("inf")))
    new_mean_delta2 = float(new_row.get("mean_delta2", float("inf")))
    error_improved = new_error_pp + 1e-9 < prev_error_pp
    delta2_improved = new_mean_delta2 + 1e-6 < prev_mean_delta2
    improved = error_improved or delta2_improved
    decision = "accepted_improvement" if improved else "rejected_regression"
    return improved, decision, prev_error_pp, new_error_pp, prev_mean_delta2, new_mean_delta2


def _extract_svg_inner(svg_text: str) -> str:
    match = re.search(r"<svg[^>]*>(.*)</svg>", svg_text, flags=re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return svg_text


def _build_transformed_svg_from_template(
    template_svg_text: str,
    target_w: int,
    target_h: int,
    *,
    rotation_deg: int,
    scale: float,
) -> str:
    inner = _extract_svg_inner(template_svg_text)
    # Keep donor stroke widths visually stable when trying scale-based transfers.
    # This mirrors the "M->S/L while preserving line thickness" workflow that is
    # often needed for noisy small/large bitmap variants.
    inner = re.sub(
        r"<(circle|ellipse|line|path|polygon|polyline|rect)\\b([^>]*)>",
        lambda m: (
            f"<{m.group(1)}{m.group(2)}>"
            if "vector-effect=" in m.group(2)
            else f"<{m.group(1)}{m.group(2)} vector-effect=\"non-scaling-stroke\">"
        ),
        inner,
        flags=re.IGNORECASE,
    )
    cx = float(target_w) / 2.0
    cy = float(target_h) / 2.0
    return (
        f'<svg width="{target_w}" height="{target_h}" viewBox="0 0 {target_w} {target_h}" '
        'xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid meet">\n'
        f'  <g transform="translate({cx:.3f} {cy:.3f}) rotate({int(rotation_deg)}) scale({float(scale):.4f}) '
        f'translate({-cx:.3f} {-cy:.3f})">\n'
        f"{inner}\n"
        "  </g>\n"
        "</svg>"
    )


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
