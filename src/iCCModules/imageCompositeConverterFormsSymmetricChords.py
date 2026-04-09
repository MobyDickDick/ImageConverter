"""Generalized helpers for circle + symmetric chord form conversion.

This module models forms like AC0204: a stroked circle with two oblique lines
that are mirrored around the horizontal circle diameter and visually terminate
at the circle border.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class SymmetricChordCircleSpec:
    """Parameterized specification for a circle with two mirrored chords."""

    cx: float
    cy: float
    r: float
    circle_fill: str = "#d9d9d9"
    circle_stroke: str = "#808080"
    circle_stroke_width: float = 1.0
    chord_stroke: str = "#808080"
    chord_stroke_width: float = 1.0
    chord_angle_deg: float = 22.0
    chord_offset: float = 4.5


@dataclass(frozen=True)
class LineSegment:
    x1: float
    y1: float
    x2: float
    y2: float


def _line_y_at_x(x: float, *, x1: float, y1: float, x2: float, y2: float) -> float:
    dx = x2 - x1
    if abs(dx) < 1e-9:
        return y1
    t = (x - x1) / dx
    return y1 + ((y2 - y1) * t)


def deriveSymmetricChordSpecImpl(
    *,
    cx: float,
    cy: float,
    r: float,
    top_line: LineSegment,
    circle_fill: str = "#d9d9d9",
    circle_stroke: str = "#808080",
    circle_stroke_width: float = 1.0,
    chord_stroke: str = "#808080",
    chord_stroke_width: float = 1.0,
) -> SymmetricChordCircleSpec:
    """Convert a concrete top-line sample into a generic symmetric chord spec."""
    dy = top_line.y2 - top_line.y1
    dx = top_line.x2 - top_line.x1
    angle_deg = math.degrees(abs(math.atan2(dy, dx)))
    y_at_center = _line_y_at_x(cx, x1=top_line.x1, y1=top_line.y1, x2=top_line.x2, y2=top_line.y2)
    chord_offset = max(0.0, cy - y_at_center)
    return SymmetricChordCircleSpec(
        cx=float(cx),
        cy=float(cy),
        r=float(r),
        circle_fill=circle_fill,
        circle_stroke=circle_stroke,
        circle_stroke_width=float(circle_stroke_width),
        chord_stroke=chord_stroke,
        chord_stroke_width=float(chord_stroke_width),
        chord_angle_deg=float(angle_deg),
        chord_offset=float(chord_offset),
    )


def _build_long_chord_segment(
    *,
    cx: float,
    cy: float,
    offset: float,
    angle_deg: float,
    width: int,
    height: int,
    mirrored: bool,
) -> LineSegment:
    # Top chord falls to the right; bottom chord is mirrored around y=cy.
    sign = 1.0 if mirrored else -1.0
    theta = math.radians(max(0.0, min(89.0, angle_deg)))
    slope = sign * math.tan(theta)

    span = float(max(width, height)) * 2.5
    x1 = cx - span
    x2 = cx + span
    base_y = cy + (offset if mirrored else -offset)
    y1 = base_y + (slope * (x1 - cx))
    y2 = base_y + (slope * (x2 - cx))
    return LineSegment(x1=x1, y1=y1, x2=x2, y2=y2)


def renderSymmetricChordCircleSvgImpl(
    width: int,
    height: int,
    spec: SymmetricChordCircleSpec,
    *,
    clip_to_inner_circle: bool = True,
) -> str:
    """Render a symmetric chord-circle SVG with clipped line ends at the circle border."""
    inner_clip_r = max(0.0, float(spec.r) - (float(spec.circle_stroke_width) / 2.0))
    top = _build_long_chord_segment(
        cx=spec.cx,
        cy=spec.cy,
        offset=spec.chord_offset,
        angle_deg=spec.chord_angle_deg,
        width=width,
        height=height,
        mirrored=False,
    )
    bottom = _build_long_chord_segment(
        cx=spec.cx,
        cy=spec.cy,
        offset=spec.chord_offset,
        angle_deg=spec.chord_angle_deg,
        width=width,
        height=height,
        mirrored=True,
    )

    clip_id = "clipCircleInner"
    elements: list[str] = [
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">',
        (
            f'  <circle cx="{spec.cx:.4f}" cy="{spec.cy:.4f}" r="{spec.r:.4f}" '
            f'fill="{spec.circle_fill}" stroke="none"/>'
        ),
    ]

    if clip_to_inner_circle:
        elements.append(
            f'  <defs><clipPath id="{clip_id}"><circle cx="{spec.cx:.4f}" cy="{spec.cy:.4f}" r="{inner_clip_r:.4f}"/></clipPath></defs>'
        )
        elements.append(f'  <g clip-path="url(#{clip_id})">')

    for line in (top, bottom):
        elements.append(
            (
                f'    <line x1="{line.x1:.4f}" y1="{line.y1:.4f}" x2="{line.x2:.4f}" y2="{line.y2:.4f}" '
                f'stroke="{spec.chord_stroke}" stroke-width="{spec.chord_stroke_width:.4f}" '
                f'stroke-linecap="round"/>'
            )
        )

    if clip_to_inner_circle:
        elements.append("  </g>")

    elements.append(
        (
            f'  <circle cx="{spec.cx:.4f}" cy="{spec.cy:.4f}" r="{spec.r:.4f}" '
            f'fill="none" stroke="{spec.circle_stroke}" stroke-width="{spec.circle_stroke_width:.4f}" '
            'stroke-linejoin="round"/>'
        )
    )
    elements.append("</svg>")
    return "\n".join(elements)
