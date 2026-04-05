"""Extracted semantic size-variant harmonization helpers for imageCompositeConverter."""

from __future__ import annotations

from collections.abc import Callable
import os


def _prototypeGroupForBase(base: str) -> str:
    if base == "AC0800":
        return "ac08_plain_ring_scale"

    if base in {"AC0811", "AC0812", "AC0813", "AC0814", "AC0831", "AC0832", "AC0833", "AC0834"}:
        return "ac08_rot_mirror_alias"

    return f"base:{base}"


def _textOrientationPolicyForBase(base: str) -> str:
    if base in {"AC0831", "AC0832", "AC0833", "AC0834"}:
        return "rotate_geometry_only"
    if base in {"AC0811", "AC0812", "AC0813", "AC0814"}:
        return "rotate_with_geometry"
    return "inherit_variant"




def captureCanonicalBadgeColorsImpl(
    params: dict,
    light_circle_fill_gray: int,
    light_circle_stroke_gray: int,
    light_circle_text_gray: int,
) -> dict:
    p = dict(params)
    p["target_fill_gray"] = int(round(float(p.get("fill_gray", light_circle_fill_gray))))
    p["target_stroke_gray"] = int(round(float(p.get("stroke_gray", light_circle_stroke_gray))))
    if p.get("stem_enabled"):
        p["target_stem_gray"] = int(round(float(p.get("stem_gray", p["target_stroke_gray"]))))
    if p.get("draw_text", True) and "text_gray" in p:
        p["target_text_gray"] = int(round(float(p.get("text_gray", light_circle_text_gray))))
    return p


def applyCanonicalBadgeColorsImpl(params: dict) -> dict:
    p = dict(params)
    if "target_fill_gray" in p:
        p["fill_gray"] = int(p["target_fill_gray"])
    if "target_stroke_gray" in p:
        p["stroke_gray"] = int(p["target_stroke_gray"])
    if p.get("stem_enabled") and "target_stem_gray" in p:
        p["stem_gray"] = int(p["target_stem_gray"])
    if p.get("draw_text", True) and "target_text_gray" in p:
        p["text_gray"] = int(p["target_text_gray"])
    return p


def needsLargeCircleOverflowGuardImpl(params: dict) -> bool:
    """Return whether circle placement may intentionally exceed canvas bounds."""
    if not bool(params.get("circle_enabled", True)):
        return False
    if bool(params.get("arm_enabled") or params.get("stem_enabled")):
        return False
    if not bool(params.get("draw_text", False)):
        return False
    if str(params.get("text_mode", "")).lower() != "co2":
        return False

    template_r = float(params.get("template_circle_radius", params.get("r", 0.0)) or 0.0)
    current_r = float(params.get("r", 0.0) or 0.0)
    width = float(params.get("width", params.get("badge_width", 0.0)) or 0.0)

    large_template = template_r >= 10.0
    large_current = current_r >= 10.0
    wide_canvas = width >= 30.0
    return bool(large_template or large_current or wide_canvas)


def scaleBadgeParamsImpl(
    anchor: dict,
    anchor_w: int,
    anchor_h: int,
    target_w: int,
    target_h: int,
    *,
    clip_scalar_fn: Callable[[float, float, float], float],
    needs_large_circle_overflow_guard_fn: Callable[[dict], bool],
) -> dict:
    scaled = dict(anchor)
    scale = max(1e-6, float(min(target_w, target_h)) / max(1.0, float(min(anchor_w, anchor_h))))
    scale_x = max(1e-6, float(target_w) / max(1.0, float(anchor_w)))
    scale_y = max(1e-6, float(target_h) / max(1.0, float(anchor_h)))

    if scaled.get("circle_enabled", True):
        scaled["cx"] = float(anchor["cx"]) * scale_x
        scaled["cy"] = float(anchor["cy"]) * scale_y
        scaled["r"] = float(anchor["r"]) * scale
        # Intentionally preserve stroke thickness across size variants.
        scaled["stroke_circle"] = float(anchor["stroke_circle"])

    if scaled.get("stem_enabled"):
        scaled["stem_x"] = float(anchor["stem_x"]) * scale_x
        scaled["stem_width"] = float(anchor["stem_width"])
        scaled["stem_top"] = float(anchor["stem_top"]) * scale_y
        scaled["stem_bottom"] = float(anchor["stem_bottom"]) * scale_y

    if scaled.get("arm_enabled"):
        scaled["arm_x1"] = float(anchor["arm_x1"]) * scale_x
        scaled["arm_y1"] = float(anchor["arm_y1"]) * scale_y
        scaled["arm_x2"] = float(anchor["arm_x2"]) * scale_x
        scaled["arm_y2"] = float(anchor["arm_y2"]) * scale_y
        scaled["arm_stroke"] = float(anchor["arm_stroke"])

    template_scalars = {
        "template_circle_cx": scale_x,
        "template_circle_cy": scale_y,
        "template_circle_radius": scale,
        "template_stem_top": scale_y,
        "template_stem_bottom": scale_y,
        "template_arm_x1": scale_x,
        "template_arm_y1": scale_y,
        "template_arm_x2": scale_x,
        "template_arm_y2": scale_y,
        "stem_len_min": scale_y,
        "arm_len_min": max(scale_x, scale_y),
    }
    for key, factor in template_scalars.items():
        if key in scaled:
            scaled[key] = float(anchor[key]) * float(factor)

    if scaled.get("circle_enabled", True):
        overflow_guard = needs_large_circle_overflow_guard_fn(scaled)
        required_r = (float(target_w) / 2.0) + 0.5 if overflow_guard else 1.0
        if overflow_guard:
            scaled["allow_circle_overflow"] = True
            scaled["circle_radius_lower_bound_px"] = float(
                max(float(scaled.get("circle_radius_lower_bound_px", 1.0)), required_r)
            )
        stroke = max(0.0, float(scaled.get("stroke_circle", 1.0)))
        half_stroke = stroke / 2.0
        cx = float(scaled.get("cx", target_w / 2.0))
        cy = float(scaled.get("cy", target_h / 2.0))
        r = max(1.0, float(scaled.get("r", 1.0)), required_r)

        max_fit_r = max(1.0, (min(float(target_w), float(target_h)) / 2.0) - half_stroke)
        if not overflow_guard and r > max_fit_r:
            r = max_fit_r

        min_cx = r + half_stroke
        max_cx = float(target_w) - r - half_stroke
        min_cy = r + half_stroke
        max_cy = float(target_h) - r - half_stroke

        if min_cx > max_cx:
            cx = float(target_w) / 2.0 if not overflow_guard else float(clip_scalar_fn(cx, 0.0, float(target_w)))
        else:
            cx = float(clip_scalar_fn(cx, min_cx, max_cx))

        if min_cy > max_cy:
            cy = float(target_h) / 2.0 if not overflow_guard else float(clip_scalar_fn(cy, 0.0, float(target_h)))
        else:
            cy = float(clip_scalar_fn(cy, min_cy, max_cy))

        if scaled.get("stem_enabled") and "stem_width" in scaled:
            stem_width = max(1e-6, float(scaled["stem_width"]))
            scaled["stem_x"] = cx - (stem_width / 2.0)
            if "stem_top" in scaled:
                bottom_anchored = float(scaled.get("stem_bottom", 0.0)) >= (float(target_h) - 0.5)
                reanchored_top = cy + r - (stem_width * 0.55)
                if bottom_anchored:
                    scaled["stem_top"] = float(clip_scalar_fn(reanchored_top, 0.0, float(target_h)))
                    scaled["stem_bottom"] = float(target_h)
                else:
                    stem_len = max(
                        1.0,
                        float(scaled.get("stem_bottom", reanchored_top))
                        - float(scaled.get("stem_top", reanchored_top)),
                    )
                    scaled["stem_top"] = float(clip_scalar_fn(reanchored_top, 0.0, float(target_h - 1)))
                    scaled["stem_bottom"] = float(
                        clip_scalar_fn(
                            float(scaled["stem_top"]) + stem_len,
                            float(scaled["stem_top"]) + 1.0,
                            float(target_h),
                        )
                    )

        scaled["cx"] = cx
        scaled["cy"] = cy
        scaled["r"] = r

    return scaled


def harmonizationAnchorPriorityImpl(suffix: str, prefer_large: bool) -> int:
    """Return size-priority rank for L/M/S harmonization anchors."""
    if prefer_large:
        return {"L": 0, "M": 1, "S": 2}.get(str(suffix), 3)
    return {"M": 0, "L": 1, "S": 2}.get(str(suffix), 3)


def clipGrayImpl(value: float) -> int:
    return int(max(0, min(255, round(float(value)))))


def familyHarmonizedBadgeColorsImpl(variant_rows: list[dict[str, object]]) -> dict[str, int]:
    """Derive a family palette from L/M/S variants and slightly boost contrast."""
    buckets: dict[str, list[float]] = {
        "fill_gray": [],
        "stroke_gray": [],
        "text_gray": [],
        "stem_gray": [],
    }
    for row in variant_rows:
        params = dict(row["params"])
        for key in buckets:
            value = params.get(key)
            if value is None:
                continue
            try:
                buckets[key].append(float(value))
            except (TypeError, ValueError):
                continue

    fill_avg = sum(buckets["fill_gray"]) / max(1, len(buckets["fill_gray"]))
    stroke_avg = sum(buckets["stroke_gray"]) / max(1, len(buckets["stroke_gray"]))
    if fill_avg < stroke_avg:
        fill_avg, stroke_avg = stroke_avg, fill_avg

    center = (fill_avg + stroke_avg) / 2.0
    delta = abs(fill_avg - stroke_avg)
    boosted_delta = max(18.0, delta * 1.12)
    fill_gray = clipGrayImpl(center + (boosted_delta / 2.0))
    stroke_gray = clipGrayImpl(center - (boosted_delta / 2.0))
    if fill_gray <= stroke_gray:
        fill_gray = clipGrayImpl(max(fill_gray, stroke_gray + 1.0))

    colors = {
        "fill_gray": fill_gray,
        "stroke_gray": stroke_gray,
        "text_gray": stroke_gray,
        "stem_gray": stroke_gray,
    }

    if buckets["text_gray"]:
        text_avg = sum(buckets["text_gray"]) / float(len(buckets["text_gray"]))
        colors["text_gray"] = clipGrayImpl(min(text_avg, float(stroke_gray)))

    if buckets["stem_gray"]:
        stem_avg = sum(buckets["stem_gray"]) / float(len(buckets["stem_gray"]))
        colors["stem_gray"] = clipGrayImpl(min(stem_avg, float(stroke_gray)))

    return colors


def harmonizeSemanticSizeVariantsImpl(
    results: list[dict[str, object]],
    folder_path: str,
    svg_out_dir: str,
    reports_out_dir: str,
    *,
    read_svg_geometry_fn: Callable[[str], tuple[int, int, dict] | None],
    normalized_geometry_signature_fn: Callable[[int, int, dict], dict[str, float]],
    max_signature_delta_fn: Callable[[dict[str, float], dict[str, float]], float],
    harmonization_anchor_priority_fn: Callable[[str, bool], int],
    family_harmonized_badge_colors_fn: Callable[[list[dict[str, object]]], dict[str, int]],
    scale_badge_params_fn: Callable[..., dict],
    generate_badge_svg_fn: Callable[[int, int, dict], str],
    render_svg_to_numpy_fn: Callable[[str, int, int], object],
    calculate_error_fn: Callable[[object, object], float],
    cv2_module,
) -> None:
    grouped: dict[str, list[dict[str, object]]] = {}
    for result in results:
        base = str(result.get("base", ""))
        grouped.setdefault(base, []).append(result)

    variant_rows_by_base: dict[str, list[dict[str, object]]] = {}
    for base, entries in sorted(grouped.items()):
        rows: list[dict[str, object]] = []
        for entry in entries:
            variant = str(entry["variant"])
            suffix = variant.rsplit("_", 1)[-1] if "_" in variant else ""
            if suffix not in {"L", "M", "S"}:
                continue
            parsed = read_svg_geometry_fn(os.path.join(svg_out_dir, f"{variant}.svg"))
            if parsed is None:
                continue
            w, h, params = parsed
            rows.append({"entry": entry, "variant": variant, "suffix": suffix, "w": w, "h": h, "params": params})
        if rows:
            variant_rows_by_base[base] = rows

    grouped_prototype_rows: dict[str, list[dict[str, object]]] = {}
    for base, rows in variant_rows_by_base.items():
        prototype_group = _prototypeGroupForBase(base)
        grouped_prototype_rows.setdefault(prototype_group, []).extend(rows)

    harmonized_logs: list[str] = []
    category_logs: list[str] = []
    for base, variant_rows in sorted(variant_rows_by_base.items()):
        if len(variant_rows) < 2:
            continue

        prototype_group = _prototypeGroupForBase(base)
        text_orientation_policy = _textOrientationPolicyForBase(base)
        prototype_rows = grouped_prototype_rows.get(prototype_group, variant_rows)

        has_text = any(bool(dict(row["params"]).get("draw_text", False)) for row in variant_rows)
        has_stem = any(bool(dict(row["params"]).get("stem_enabled", False)) for row in variant_rows)
        has_arm = any(bool(dict(row["params"]).get("arm_enabled", False)) for row in variant_rows)
        has_connector = has_stem or has_arm
        category = "Kreise mit Buchstaben" if has_text and not has_connector else (
            "Kreise ohne Buchstaben" if (not has_text and not has_connector) else (
                "Kellen mit Buchstaben" if has_text else "Kellen ohne Buchstaben"
            )
        )
        variants_joined = "|".join(sorted(str(r["variant"]) for r in variant_rows))

        sigs = {
            str(row["variant"]): normalized_geometry_signature_fn(int(row["w"]), int(row["h"]), dict(row["params"]))
            for row in variant_rows
        }
        prototype_sigs = {
            str(row["variant"]): normalized_geometry_signature_fn(int(row["w"]), int(row["h"]), dict(row["params"]))
            for row in prototype_rows
        }
        max_delta = 0.0
        for i in range(len(variant_rows)):
            for j in range(i + 1, len(variant_rows)):
                vi = str(variant_rows[i]["variant"])
                vj = str(variant_rows[j]["variant"])
                max_delta = max(max_delta, max_signature_delta_fn(sigs[vi], sigs[vj]))
        prototype_delta = max_delta
        if prototype_rows:
            prototype_delta = 0.0
            for target in variant_rows:
                target_variant = str(target["variant"])
                target_sig = sigs[target_variant]
                deltas = [max_signature_delta_fn(target_sig, prototype_sigs[str(proto["variant"])]) for proto in prototype_rows]
                if deltas:
                    prototype_delta = max(prototype_delta, min(deltas))
        category_logs.append(
            (
                f"{base};{category};{variants_joined};{prototype_group};"
                f"{prototype_delta:.4f};{text_orientation_policy}"
            )
        )

        def _anchorRank(row: dict[str, object]) -> tuple[int, float]:
            suffix = str(row.get("suffix", ""))
            priority = harmonization_anchor_priority_fn(suffix, has_connector)
            err = float(dict(row["entry"]).get("error", float("inf")))
            return priority, err

        anchor = min(prototype_rows, key=_anchorRank)
        anchor_variant = str(anchor["variant"])
        anchor_w = int(anchor["w"])
        anchor_h = int(anchor["h"])
        anchor_params = dict(anchor["params"])
        family_colors = family_harmonized_badge_colors_fn(variant_rows)

        for row in variant_rows:
            target_variant = str(row["variant"])
            target_w = int(row["w"])
            target_h = int(row["h"])
            scaled = scale_badge_params_fn(
                anchor_params,
                anchor_w,
                anchor_h,
                target_w,
                target_h,
                target_variant=target_variant,
            )
            scaled.update(family_colors)
            if scaled.get("draw_text"):
                scaled["text_gray"] = int(family_colors["text_gray"])
            if scaled.get("stem_enabled"):
                scaled["stem_gray"] = int(family_colors["stem_gray"])
            svg = generate_badge_svg_fn(target_w, target_h, scaled)

            target_filename = str(dict(row["entry"])["filename"])
            target_path = os.path.join(folder_path, target_filename)
            target_img = cv2_module.imread(target_path)
            if target_img is None:
                harmonized_logs.append(f"{base}: {target_variant} übersprungen (Bild fehlt: {target_filename})")
                continue

            rendered = render_svg_to_numpy_fn(svg, target_w, target_h)
            candidate_error = calculate_error_fn(target_img, rendered)
            baseline_error = float(dict(row["entry"]).get("error", float("inf")))
            if candidate_error > baseline_error + 0.25:
                harmonized_logs.append(
                    (
                        f"{base}: {target_variant} nicht harmonisiert "
                        f"(Fehler {candidate_error:.2f} > Basis {baseline_error:.2f})"
                    )
                )
                continue

            with open(os.path.join(svg_out_dir, f"{target_variant}.svg"), "w", encoding="utf-8") as f:
                f.write(svg)
            harmonized_logs.append(
                (
                    f"{base}: {target_variant} aus {anchor_variant} harmonisiert "
                    f"(prototype_group={prototype_group}, max_delta={prototype_delta:.4f}, "
                    f"text_orientation_policy={text_orientation_policy}, "
                    f"Fehler {baseline_error:.2f}->{candidate_error:.2f}, "
                    f"Farben fill/stroke={family_colors['fill_gray']}/{family_colors['stroke_gray']})"
                )
            )

    if harmonized_logs:
        with open(os.path.join(reports_out_dir, "variant_harmonization.log"), "w", encoding="utf-8") as f:
            f.write("\n".join(harmonized_logs).rstrip() + "\n")
    if category_logs:
        with open(os.path.join(reports_out_dir, "shape_catalog.csv"), "w", encoding="utf-8") as f:
            f.write("base;category;variants;prototype_group;geometry_signature_delta;text_orientation_policy\n")
            f.write("\n".join(category_logs).rstrip() + "\n")
