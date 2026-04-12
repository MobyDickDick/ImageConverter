from __future__ import annotations

import math


def estimateStrokeStyleImpl(grayscale, element, candidate, *, gray_to_hex_fn):
    vals = [grayscale[y + element.y0][x + element.x0] for y, row in enumerate(element.pixels) for x, v in enumerate(row) if v]
    fill = gray_to_hex_fn(sum(vals) / max(1, len(vals)))
    if candidate.shape != "circle":
        return fill, None, None
    r = max(1.0, (candidate.w + candidate.h) / 4.0)
    inner = []
    outer = []
    for y, row in enumerate(element.pixels):
        for x, v in enumerate(row):
            if not v:
                continue
            d = ((x - candidate.cx) ** 2 + (y - candidate.cy) ** 2) ** 0.5
            px = grayscale[y + element.y0][x + element.x0]
            if d >= r * 0.84:
                outer.append(px)
            elif d <= r * 0.65:
                inner.append(px)
    if outer and inner and (sum(outer) / len(outer)) < (sum(inner) / len(inner)) - 10:
        return gray_to_hex_fn(sum(inner) / len(inner)), gray_to_hex_fn(sum(outer) / len(outer)), max(1.0, r * 0.2)
    return fill, None, None


def candidateToSvgImpl(candidate, gx: int, gy: int, fill_color: str, stroke_color: str | None = None, stroke_width: float | None = None) -> str:
    if candidate.shape == "circle":
        r = max(1.0, (candidate.w + candidate.h) / 4.0)
        if stroke_color is not None and stroke_width is not None:
            r = max(0.5, r - (float(stroke_width) / 2.0))
        stroke_attr = "" if stroke_color is None else f' stroke="{stroke_color}" stroke-width="{float(stroke_width or 1.0):.2f}"'
        return f'<circle cx="{candidate.cx + gx:.2f}" cy="{candidate.cy + gy:.2f}" r="{r:.2f}" fill="{fill_color}"{stroke_attr} />'
    rx = max(1.0, candidate.w / 2.0)
    ry = max(1.0, candidate.h / 2.0)
    return f'<ellipse cx="{candidate.cx + gx:.2f}" cy="{candidate.cy + gy:.2f}" rx="{rx:.2f}" ry="{ry:.2f}" fill="{fill_color}" />'


def decomposeCircleWithStemImpl(grayscale, element, candidate, *, candidate_to_svg_fn, estimate_stroke_style_fn):
    if not element.pixels or not element.pixels[0]:
        return None

    r = max(1.0, (candidate.w + candidate.h) / 4.0)
    cx = float(candidate.cx)
    cy = float(candidate.cy)

    residual = []
    circle_pixels = []
    for y, row in enumerate(element.pixels):
        for x, v in enumerate(row):
            if not v:
                continue
            d = math.hypot(float(x) - cx, float(y) - cy)
            if d <= (r * 1.02):
                circle_pixels.append((x, y))
            elif d >= (r * 0.90):
                residual.append((x, y))

    if not residual:
        return None

    residual_set = set(residual)
    visited = set()
    best_cluster = []
    for seed in residual:
        if seed in visited:
            continue
        stack = [seed]
        cluster = []
        visited.add(seed)
        while stack:
            px, py = stack.pop()
            cluster.append((px, py))
            for nx, ny in ((px - 1, py), (px + 1, py), (px, py - 1), (px, py + 1)):
                if (nx, ny) in residual_set and (nx, ny) not in visited:
                    visited.add((nx, ny))
                    stack.append((nx, ny))
        if len(cluster) > len(best_cluster):
            best_cluster = cluster

    if not best_cluster:
        return None

    xs = [p[0] for p in best_cluster]
    ys = [p[1] for p in best_cluster]
    if len(xs) < 4 or len(ys) < 4:
        return None

    bbox_w = max(xs) - min(xs) + 1
    bbox_h = max(ys) - min(ys) + 1
    area = len(best_cluster)
    if area < max(8, int(0.03 * max(1.0, math.pi * r * r))):
        return None
    if bbox_w < 2 or bbox_h < 2:
        return None

    radial = [math.hypot(float(x) - cx, float(y) - cy) for x, y in best_cluster]
    if not radial:
        return None
    mean_r = sum(radial) / len(radial)
    radial_span = max(radial) - min(radial)

    horizontal = bbox_w >= bbox_h
    if horizontal:
        if bbox_w < r * 0.35 or bbox_h > r * 1.05:
            return None
        x_min, x_max = min(xs), max(xs)
        y_mid = sum(ys) / len(ys)
        sign = -1.0 if x_max < cx else (1.0 if x_min > cx else 0.0)
        if sign == 0.0:
            sign = -1.0 if (cx - x_min) > (x_max - cx) else 1.0
        line_y = y_mid
        line_x1 = cx + sign * r * 0.95
        line_x2 = float(x_min) if sign < 0 else float(x_max)
        if abs(line_x2 - line_x1) < max(2.0, r * 0.2):
            line_x2 = cx + sign * max(r * 1.35, abs(line_x2 - cx))
        stroke = max(1.0, min(float(bbox_h), r * 0.45))
        stem_svg = f'<line x1="{line_x1 + element.x0:.2f}" y1="{line_y + element.y0:.2f}" x2="{line_x2 + element.x0:.2f}" y2="{line_y + element.y0:.2f}" stroke="#000000" stroke-width="{stroke:.2f}" stroke-linecap="round" />'
    else:
        if bbox_h < r * 0.35 or bbox_w > r * 1.05:
            return None
        y_min, y_max = min(ys), max(ys)
        x_mid = sum(xs) / len(xs)
        sign = -1.0 if y_max < cy else (1.0 if y_min > cy else 0.0)
        if sign == 0.0:
            sign = -1.0 if (cy - y_min) > (y_max - cy) else 1.0
        line_x = x_mid
        line_y1 = cy + sign * r * 0.95
        line_y2 = float(y_min) if sign < 0 else float(y_max)
        if abs(line_y2 - line_y1) < max(2.0, r * 0.2):
            line_y2 = cy + sign * max(r * 1.35, abs(line_y2 - cy))
        stroke = max(1.0, min(float(bbox_w), r * 0.45))
        stem_svg = f'<line x1="{line_x + element.x0:.2f}" y1="{line_y1 + element.y0:.2f}" x2="{line_x + element.x0:.2f}" y2="{line_y2 + element.y0:.2f}" stroke="#000000" stroke-width="{stroke:.2f}" stroke-linecap="round" />'

    coverage = len(best_cluster) / max(1.0, len(circle_pixels))
    if coverage > 0.75 and radial_span < max(2.0, r * 0.35):
        return None
    if abs(mean_r - r) > max(2.5, r * 0.45):
        return None

    fill_color, stroke_color, stroke_width = estimate_stroke_style_fn(grayscale, element, candidate)
    circle_svg = candidate_to_svg_fn(candidate, element.x0, element.y0, fill_color, stroke_color, stroke_width)
    return [circle_svg, stem_svg]
