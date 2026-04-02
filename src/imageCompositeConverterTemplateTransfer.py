"""Extracted template-transfer helpers for imageCompositeConverter."""

from __future__ import annotations

import math
import re
from collections.abc import Callable


def extractSvgInnerImpl(svg_text: str) -> str:
    match = re.search(r"<svg[^>]*>(.*)</svg>", svg_text, flags=re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return svg_text


def buildTransformedSvgFromTemplateImpl(
    template_svg_text: str,
    target_w: int,
    target_h: int,
    *,
    rotation_deg: int,
    scale: float,
    extract_svg_inner_fn: Callable[[str], str],
) -> str:
    inner = extract_svg_inner_fn(template_svg_text)
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


def templateTransferScaleCandidatesImpl(base_scale: float) -> list[float]:
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


def estimateTemplateTransferScaleImpl(
    img_orig: object,
    donor_svg_text: str,
    target_w: int,
    target_h: int,
    *,
    rotation_deg: int,
    render_svg_to_numpy_fn: Callable[[str, int, int], object],
    build_transformed_svg_from_template_fn: Callable[..., str],
    foreground_mask_fn: Callable[[object], object],
    mask_bbox_fn: Callable[[object], tuple[int, int, int, int] | None],
) -> float | None:
    rendered = render_svg_to_numpy_fn(
        build_transformed_svg_from_template_fn(
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

    target_mask = foreground_mask_fn(img_orig)
    donor_mask = foreground_mask_fn(rendered)
    target_bbox = mask_bbox_fn(target_mask)
    donor_bbox = mask_bbox_fn(donor_mask)
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


def templateTransferTransformCandidatesImpl(
    target_variant: str,
    donor_variant: str,
    *,
    estimated_scale_by_rotation: dict[int, float] | None = None,
    template_transfer_scale_candidates_fn: Callable[[float], list[float]],
) -> list[tuple[int, float]]:
    del target_variant, donor_variant

    candidates: list[tuple[int, float]] = []
    seen: set[tuple[int, float]] = set()
    for rotation in (0, 90, 180, 270):
        estimated = None
        if estimated_scale_by_rotation is not None:
            estimated = estimated_scale_by_rotation.get(rotation)
        for scale in template_transfer_scale_candidates_fn(estimated if estimated is not None else 1.0):
            candidate = (rotation, float(scale))
            key = (rotation, round(float(scale), 4))
            if key in seen:
                continue
            seen.add(key)
            candidates.append(candidate)
    return candidates


def rankTemplateTransferDonorsImpl(
    target_row: dict[str, object],
    donor_rows: list[dict[str, object]],
    *,
    normalized_geometry_signature_fn: Callable[[int, int, dict], dict[str, float]],
    max_signature_delta_fn: Callable[[dict[str, float], dict[str, float]], float],
) -> list[dict[str, object]]:
    target_base = str(target_row.get("base", "")).upper()
    target_sig: dict[str, float] | None = None
    target_params = target_row.get("params")
    if isinstance(target_params, dict):
        target_sig = normalized_geometry_signature_fn(
            int(target_row.get("w", 0)),
            int(target_row.get("h", 0)),
            dict(target_params),
        )

    ranked: list[tuple[tuple[float, float, float], dict[str, object]]] = []
    for donor in donor_rows:
        donor_base = str(donor.get("base", "")).upper()
        donor_error_pp = float(donor.get("error_per_pixel", float("inf")))
        donor_sig: dict[str, float] | None = None
        donor_params = donor.get("params")
        if isinstance(donor_params, dict):
            donor_sig = normalized_geometry_signature_fn(int(donor.get("w", 0)), int(donor.get("h", 0)), dict(donor_params))

        delta = float("inf")
        if target_sig is not None and donor_sig is not None:
            delta = max_signature_delta_fn(target_sig, donor_sig)

        key = (0.0 if donor_base == target_base else 1.0, delta, donor_error_pp)
        ranked.append((key, donor))

    ranked.sort(key=lambda item: item[0])
    return [donor for _, donor in ranked]


def templateTransferDonorFamilyCompatibleImpl(
    target_base: str,
    donor_base: str,
    *,
    documented_alias_refs: set[str] | None = None,
    extract_symbol_family_fn: Callable[[str], str | None],
) -> bool:
    alias_refs = {str(v).upper() for v in (documented_alias_refs or set()) if str(v).strip()}
    if donor_base.upper() in alias_refs:
        return True

    target_family = extract_symbol_family_fn(target_base)
    donor_family = extract_symbol_family_fn(donor_base)
    if target_family is None or donor_family is None:
        return True
    return target_family == donor_family
