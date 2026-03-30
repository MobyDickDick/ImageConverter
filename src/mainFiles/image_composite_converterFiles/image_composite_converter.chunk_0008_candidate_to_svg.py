def candidate_to_svg(candidate: Candidate, gx: int, gy: int, fill_color: str, stroke_color: str | None = None, stroke_width: float | None = None) -> str:
    if candidate.shape == 'circle':
        r = max(1.0, (candidate.w + candidate.h) / 4.0)
        if stroke_color is not None and stroke_width is not None:
            r = max(0.5, r - (float(stroke_width) / 2.0))
        stroke_attr = '' if stroke_color is None else f' stroke="{stroke_color}" stroke-width="{float(stroke_width or 1.0):.2f}"'
        return f'<circle cx="{candidate.cx + gx:.2f}" cy="{candidate.cy + gy:.2f}" r="{r:.2f}" fill="{fill_color}"{stroke_attr} />'
    rx = max(1.0, candidate.w / 2.0)
    ry = max(1.0, candidate.h / 2.0)
    return f'<ellipse cx="{candidate.cx + gx:.2f}" cy="{candidate.cy + gy:.2f}" rx="{rx:.2f}" ry="{ry:.2f}" fill="{fill_color}" />'


