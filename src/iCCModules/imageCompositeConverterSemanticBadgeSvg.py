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
    defs: list[str] = []

    if str(p.get("head_style", "")).lower() == "ac0223_triple_valve":
        defs.append("  <linearGradient id=\"ac0223ValveGradient\" x1=\"1\" y1=\"0\" x2=\"0\" y2=\"1\">")
        defs.append(f'    <stop offset="0%" stop-color="{str(p.get("head_gradient_dark", "#b2b2b3"))}"/>')
        defs.append(f'    <stop offset="100%" stop-color="{str(p.get("head_gradient_light", "#d9d9d9"))}"/>')
        defs.append("  </linearGradient>")
    if defs:
        elements.append("  <defs>")
        elements.extend(defs)
        elements.append("  </defs>")

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
                f'stroke="{str(p.get("arm_color", grayhex_fn(p.get("stroke_gray", 152))))}" '
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

    if str(p.get("head_style", "")).lower() == "ac0223_triple_valve":
        sx = float(w) / 50.0 if w > 0 else 1.0
        sy = float(h) / 75.0 if h > 0 else 1.0
        head_stroke = str(p.get("head_stroke", "#808080"))
        head_hub_fill = str(p.get("head_hub_fill", "#7f7f7f"))
        hub_cx = float(p.get("head_hub_cx", p.get("arm_x2", p.get("cx", float(w) / 2.0))))
        hub_cy = float(p.get("head_hub_cy", p.get("arm_y2", 25.153 * sy)))
        tx = hub_cx - (25.0 * sx)
        ty = hub_cy - (25.153 * sy)
        elements.append(f'  <g transform="translate({tx:.6f} {ty:.6f}) scale({sx:.6f} {sy:.6f})">')
        elements.append(
            '    <path d="M 36.492188 3.0410156 L 13.505859 3.1347656 L 23.417969 22.871094 '
            'A 2.5 2.500001 0 0 0 22.748047 23.722656 L 2.0195312 13.308594 L 2.1113281 36.294922 '
            'L 22.75 25.882812 A 2.5 2.500001 0 0 0 25 27.300781 A 2.5 2.500001 0 0 0 27.207031 25.962891 '
            'L 47.78125 36.294922 L 47.873047 13.308594 L 27.212891 23.640625 A 2.5 2.500001 0 0 0 26.580078 '
            '22.863281 L 36.492188 3.0410156 z" fill="url(#ac0223ValveGradient)" stroke="none"/>'
        )
        elements.append(
            f'    <polygon points="36.492188,2.6959677 47.87305,12.963546 47.78125,35.949874 2.1132824,35.949874 2.0195324,12.963546 13.50586,2.7897177" fill="#d9d9d9" stroke="{head_stroke}" stroke-width="1"/>'
        )
        elements.append(f'    <ellipse cx="25" cy="25.153" rx="2.5" ry="2.500001" fill="{head_hub_fill}" stroke="{head_stroke}" stroke-width="1"/>')
        elements.append("  </g>")

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
