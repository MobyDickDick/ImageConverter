"""Extracted template-transfer helpers for imageCompositeConverter."""

from __future__ import annotations

import math
import os
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


def tryTemplateTransferImpl(
    *,
    target_row: dict[str, object],
    donor_rows: list[dict[str, object]],
    folder_path: str,
    svg_out_dir: str,
    diff_out_dir: str,
    rng: object | None = None,
    deterministic_order: bool = False,
    cv2_module: object,
    read_svg_geometry_fn: Callable[[str], tuple[int, int, dict[str, object]] | None],
    rank_template_transfer_donors_fn: Callable[[dict[str, object], list[dict[str, object]]], list[dict[str, object]]],
    template_transfer_donor_family_compatible_fn: Callable[..., bool],
    semantic_transfer_is_compatible_fn: Callable[[dict[str, object], dict[str, object]], bool],
    semantic_transfer_scale_candidates_fn: Callable[[float], list[float]],
    semantic_transfer_rotations_fn: Callable[[dict[str, object], dict[str, object]], tuple[int, ...]],
    semantic_transfer_badge_params_fn: Callable[..., dict[str, object]],
    estimate_template_transfer_scale_fn: Callable[..., float | None],
    template_transfer_transform_candidates_fn: Callable[..., list[tuple[int, float]]],
    build_transformed_svg_from_template_fn: Callable[..., str],
    render_svg_to_numpy_fn: Callable[[str, int, int], object],
    calculate_error_fn: Callable[[object, object], float],
    create_diff_image_fn: Callable[[object, object], object],
    calculate_delta2_stats_fn: Callable[[object, object], tuple[float, float]],
    generate_badge_svg_fn: Callable[[int, int, dict[str, object]], str],
) -> tuple[dict[str, object] | None, dict[str, object] | None]:
    filename = str(target_row.get("filename", ""))
    if not filename:
        return None, None

    img_path = os.path.join(folder_path, filename)
    img_orig = cv2_module.imread(img_path)
    if img_orig is None:
        return None, None

    h, w = img_orig.shape[:2]
    pixel_count = float(max(1, w * h))
    prev_error_pp = float(target_row.get("error_per_pixel", float("inf")))

    best_svg: str | None = None
    best_error = float(target_row.get("best_error", float("inf")))
    best_error_pp = prev_error_pp
    best_donor = ""
    best_rotation = 0
    best_scale = 1.0

    target_variant = str(target_row.get("variant", "")).upper()
    target_base = str(target_row.get("base", "")).upper()
    if target_base == "AC0223":
        # AC0223 includes a dedicated valve-head overlay that is not encoded in
        # generic geometry extraction. Transferring donor templates can drop the
        # polygon/hub semantics, so keep native conversion output only.
        return None, None
    target_svg_path = os.path.join(svg_out_dir, f"{target_variant}.svg")
    target_svg_geometry = read_svg_geometry_fn(target_svg_path)
    target_geom_params = dict(target_svg_geometry[2]) if target_svg_geometry is not None else None
    target_params_raw = target_row.get("params")
    target_alias_refs: set[str] = set()
    if isinstance(target_params_raw, dict):
        alias_values = target_params_raw.get("documented_alias_refs", [])
        if isinstance(alias_values, list):
            target_alias_refs = {str(v).upper() for v in alias_values if str(v).strip()}
    target_is_semantic = isinstance(target_params_raw, dict) and str(target_params_raw.get("mode", "")) == "semantic_badge"
    ordered_donors = rank_template_transfer_donors_fn(target_row, donor_rows)
    if rng is not None and not deterministic_order and len(ordered_donors) > 1:
        head = ordered_donors[:3]
        tail = ordered_donors[3:]
        rng.shuffle(head)
        ordered_donors = head + tail
    for donor in ordered_donors:
        donor_variant = str(donor.get("variant", "")).upper()
        donor_base = str(donor.get("base", "")).upper()
        if not donor_variant or donor_variant == target_variant:
            continue
        if not target_is_semantic and not template_transfer_donor_family_compatible_fn(
            target_base,
            donor_base,
            documented_alias_refs=target_alias_refs,
        ):
            continue
        donor_svg_path = os.path.join(svg_out_dir, f"{donor_variant}.svg")
        if not os.path.exists(donor_svg_path):
            continue
        try:
            donor_svg_text = open(donor_svg_path, "r", encoding="utf-8").read()
        except OSError:
            continue

        donor_svg_geometry = read_svg_geometry_fn(donor_svg_path)
        donor_geom_params = dict(donor_svg_geometry[2]) if donor_svg_geometry is not None else None

        donor_params_raw = donor.get("params")
        donor_is_semantic = isinstance(donor_params_raw, dict) and str(donor_params_raw.get("mode", "")) == "semantic_badge"
        if target_is_semantic and not donor_is_semantic:
            continue

        if isinstance(target_params_raw, dict) and isinstance(donor_params_raw, dict):
            if (
                target_is_semantic
                and donor_is_semantic
                and target_geom_params is not None
                and donor_geom_params is not None
                and semantic_transfer_is_compatible_fn(dict(target_params_raw), dict(donor_params_raw))
            ):
                base_scale = float(min(w, h)) / max(1.0, float(min(int(donor.get("w", w)), int(donor.get("h", h)))))
                semantic_scales = semantic_transfer_scale_candidates_fn(base_scale)
                if rng is not None and not deterministic_order:
                    keep = semantic_scales[:2]
                    rest = semantic_scales[2:]
                    rng.shuffle(rest)
                    semantic_scales = keep + rest
                for rotation in semantic_transfer_rotations_fn(dict(target_params_raw), dict(donor_params_raw)):
                    for scale in semantic_scales:
                        candidate_params = semantic_transfer_badge_params_fn(
                            dict(donor_geom_params),
                            dict(target_geom_params),
                            target_w=w,
                            target_h=h,
                            rotation_deg=rotation,
                            scale=float(scale),
                        )
                        try:
                            candidate_svg = generate_badge_svg_fn(w, h, candidate_params)
                            rendered = render_svg_to_numpy_fn(candidate_svg, w, h)
                        except Exception:
                            continue
                        error = calculate_error_fn(img_orig, rendered)
                        error_pp = float(error) / pixel_count
                        if error_pp + 1e-9 < best_error_pp:
                            best_error = float(error)
                            best_error_pp = error_pp
                            best_svg = candidate_svg
                            best_donor = donor_variant
                            best_rotation = rotation
                            best_scale = float(scale)

        if target_is_semantic:
            continue

        estimated_scales = {
            rotation: estimate_template_transfer_scale_fn(
                img_orig,
                donor_svg_text,
                w,
                h,
                rotation_deg=rotation,
            )
            for rotation in (0, 90, 180, 270)
        }

        for rotation, scale in template_transfer_transform_candidates_fn(
            target_variant,
            donor_variant,
            estimated_scale_by_rotation=estimated_scales,
        ):
            candidate_svg = build_transformed_svg_from_template_fn(
                donor_svg_text,
                w,
                h,
                rotation_deg=rotation,
                scale=scale,
            )
            rendered = render_svg_to_numpy_fn(candidate_svg, w, h)
            error = calculate_error_fn(img_orig, rendered)
            error_pp = float(error) / pixel_count
            if error_pp + 1e-9 < best_error_pp:
                best_error = float(error)
                best_error_pp = error_pp
                best_svg = candidate_svg
                best_donor = donor_variant
                best_rotation = rotation
                best_scale = scale

    if best_svg is None:
        return None, None

    stem = os.path.splitext(filename)[0]
    svg_path = os.path.join(svg_out_dir, f"{stem}.svg")
    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(best_svg)

    rendered = render_svg_to_numpy_fn(best_svg, w, h)
    mean_delta2 = float(target_row.get("mean_delta2", float("inf")))
    std_delta2 = float(target_row.get("std_delta2", float("inf")))
    if rendered is not None:
        diff = create_diff_image_fn(img_orig, rendered)
        cv2_module.imwrite(os.path.join(diff_out_dir, f"{stem}_diff.png"), diff)
        try:
            mean_delta2, std_delta2 = calculate_delta2_stats_fn(img_orig, rendered)
        except Exception:
            mean_delta2 = float(target_row.get("mean_delta2", float("inf")))
            std_delta2 = float(target_row.get("std_delta2", float("inf")))

    updated_row = dict(target_row)
    updated_row["best_error"] = float(best_error)
    updated_row["error_per_pixel"] = float(best_error_pp)
    updated_row["mean_delta2"] = float(mean_delta2)
    updated_row["std_delta2"] = float(std_delta2)

    detail = {
        "filename": filename,
        "donor_variant": best_donor,
        "rotation_deg": int(best_rotation),
        "scale": float(best_scale),
        "old_error_per_pixel": float(prev_error_pp),
        "new_error_per_pixel": float(best_error_pp),
        "old_mean_delta2": float(target_row.get("mean_delta2", float("inf"))),
        "new_mean_delta2": float(mean_delta2),
    }
    return updated_row, detail
