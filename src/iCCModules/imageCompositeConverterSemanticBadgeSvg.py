"""Semantic badge SVG generation extracted from the converter monolith."""

from __future__ import annotations

from typing import Callable


def generateBadgeSvgImpl(
    w: int,
    h: int,
    params: dict,
    *,
    align_stem_to_circle_center_fn: Callable[[dict], dict],
    quantize_badge_params_fn: Callable[[dict, int, int], dict],
    clip_scalar_fn: Callable[[float, float, float], float],
    grayhex_fn: Callable[[float], str],
    co2_layout_fn: Callable[[dict], dict[str, float]],
    t_path_d: str,
    t_xmin: float,
    t_ymax: float,
    m_path_d: str,
    m_xmin: float,
    m_ymax: float,
) -> str:
    """Build a semantic badge SVG from quantized parameters."""
    p = align_stem_to_circle_center_fn(dict(params))
    p = quantize_badge_params_fn(p, w, h)
    elements = [f'<svg width="{w}px" height="{h}px" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">']

    background_fill = p.get("background_fill")
    if background_fill:
        elements.append(f'  <rect x="0" y="0" width="{float(w):.4f}" height="{float(h):.4f}" fill="{background_fill}"/>')

    if p.get("arm_enabled"):
        arm_x1 = float(clip_scalar_fn(float(p.get("arm_x1", 0.0)), 0.0, float(w)))
        arm_y1 = float(clip_scalar_fn(float(p.get("arm_y1", p.get("arm_y", 0.0))), 0.0, float(h)))
        arm_x2 = float(clip_scalar_fn(float(p.get("arm_x2", 0.0)), 0.0, float(w)))
        arm_y2 = float(clip_scalar_fn(float(p.get("arm_y2", p.get("arm_y", arm_y1))), 0.0, float(h)))
        arm_stroke = float(p["arm_stroke"])

        elements.append(
            (
                f'  <line x1="{arm_x1:.4f}" y1="{arm_y1:.4f}" '
                f'x2="{arm_x2:.4f}" y2="{arm_y2:.4f}" '
                f'stroke="{grayhex_fn(p.get("stroke_gray", 152))}" '
                f'stroke-width="{arm_stroke:.4f}" stroke-linecap="round"/>'
            )
        )

    if p.get("stem_enabled"):
        stem_x = float(clip_scalar_fn(float(p.get("stem_x", 0.0)), 0.0, float(w)))
        stem_top = float(clip_scalar_fn(float(p.get("stem_top", 0.0)), 0.0, float(h)))
        stem_width = max(0.0, min(float(p.get("stem_width", 0.0)), max(0.0, float(w) - stem_x)))
        stem_bottom = float(clip_scalar_fn(float(p.get("stem_bottom", 0.0)), stem_top, float(h)))
        elements.append(
            (
                f'  <rect x="{stem_x:.4f}" y="{stem_top:.4f}" '
                f'width="{stem_width:.4f}" height="{max(0.0, stem_bottom - stem_top):.4f}" '
                f'fill="{grayhex_fn(p.get("stem_gray", p["stroke_gray"]))}"/>'
            )
        )

    if p.get("circle_enabled", True):
        elements.append(
            (
                f'  <circle cx="{p["cx"]:.4f}" cy="{p["cy"]:.4f}" r="{p["r"]:.4f}" '
                f'fill="{grayhex_fn(p["fill_gray"])}" stroke="{grayhex_fn(p["stroke_gray"])}" '
                f'stroke-width="{p["stroke_circle"]:.4f}"/>'
            )
        )

    if p.get("draw_text", True):
        if p.get("text_mode") == "path_t":
            elements.append(
                (
                    f'  <path d="{t_path_d}" fill="{grayhex_fn(p["text_gray"])}" '
                    f'transform="translate({p["tx"]:.4f},{p["ty"]:.4f}) '
                    f'scale({p["s"]:.6f},{-p["s"]:.6f}) '
                    f'translate({-t_xmin},{-t_ymax})"/>'
                )
            )
        elif p.get("text_mode") == "co2":
            layout = co2_layout_fn(p)
            font_size = float(layout["font_size"])
            y_text = float(layout["y_base"])
            width_scale = float(layout.get("width_scale", 1.0))
            elements.append(
                (
                    f'  <text x="{float(layout["co_x"]):.4f}" y="{y_text:.4f}" fill="{grayhex_fn(p["text_gray"])}" '
                    f'font-family="Arial, Helvetica, sans-serif" font-size="{font_size:.4f}px" '
                    f'font-style="normal" font-weight="600" text-anchor="middle" dominant-baseline="middle" '
                    f'transform="translate({float(layout["co_x"]):.4f} {y_text:.4f}) scale({width_scale:.4f} 1) '
                    f'translate({-float(layout["co_x"]):.4f} {-y_text:.4f})">CO</text>'
                )
            )
            elements.append(
                (
                    f'  <text x="{float(layout["subscript_x"]):.4f}" y="{float(layout["subscript_y"]):.4f}" fill="{grayhex_fn(p["text_gray"])}" '
                    f'font-family="Arial, Helvetica, sans-serif" font-size="{float(layout["sub_font_px"]):.4f}px" '
                    f'font-style="normal" font-weight="600" text-anchor="start" dominant-baseline="middle" '
                    f'transform="translate({float(layout["subscript_x"]):.4f} {float(layout["subscript_y"]):.4f}) scale({width_scale:.4f} 1) '
                    f'translate({-float(layout["subscript_x"]):.4f} {-float(layout["subscript_y"]):.4f})">2</text>'
                )
            )
        elif p.get("text_mode") == "voc":
            radius = p.get("r", min(w, h) * 0.4)
            font_size = max(4.0, radius * p.get("voc_font_scale", 0.52))
            voc_dy = p.get("voc_dy", 0.0)
            voc_weight = int(p.get("voc_weight", 600))
            elements.append(
                (
                    f'  <text x="{p["cx"]:.4f}" y="{(p["cy"] + voc_dy):.4f}" fill="{grayhex_fn(p["text_gray"])}" '
                    f'font-family="Arial, Helvetica, sans-serif" font-size="{font_size:.4f}px" '
                    f'font-style="normal" font-weight="{voc_weight}" letter-spacing="0.01em" '
                    f'text-anchor="middle" dominant-baseline="middle">VOC</text>'
                )
            )
        else:
            elements.append(
                (
                    f'  <path d="{m_path_d}" fill="{grayhex_fn(p["text_gray"])}" '
                    f'transform="translate({p["tx"]:.4f},{p["ty"]:.4f}) '
                    f'scale({p["s"]:.6f},{-p["s"]:.6f}) '
                    f'translate({-m_xmin},{-m_ymax})"/>'
                )
            )

    elements.append("</svg>")
    return "\n".join(elements)
