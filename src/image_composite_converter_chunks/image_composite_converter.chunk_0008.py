def decompose_circle_with_stem(grayscale: list[list[int]], element: Element, candidate: Candidate) -> list[str] | None:
    if not element.pixels or not element.pixels[0]:
        return None

    r = max(1.0, (candidate.w + candidate.h) / 4.0)
    cx = float(candidate.cx)
    cy = float(candidate.cy)

    # Residual foreground outside the candidate circle corresponds to connectors.
    residual: list[tuple[int, int]] = []
    circle_pixels: list[tuple[int, int]] = []
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

    # Keep only the dominant connected residual cluster.
    residual_set = set(residual)
    visited: set[tuple[int, int]] = set()
    best_cluster: list[tuple[int, int]] = []
    for seed in residual:
        if seed in visited:
            continue
        stack = [seed]
        cluster: list[tuple[int, int]] = []
        visited.add(seed)
        while stack:
            px, py = stack.pop()
            cluster.append((px, py))
            for nx, ny in ((px + 1, py), (px - 1, py), (px, py + 1), (px, py - 1)):
                if (nx, ny) in residual_set and (nx, ny) not in visited:
                    visited.add((nx, ny))
                    stack.append((nx, ny))
        if len(cluster) > len(best_cluster):
            best_cluster = cluster

    if not best_cluster:
        return None

    xs = [x for x, _ in best_cluster]
    ys = [y for _, y in best_cluster]
    sx0, sx1 = min(xs), max(xs)
    sy0, sy1 = min(ys), max(ys)
    stem_w = max(1, sx1 - sx0 + 1)
    stem_h = max(1, sy1 - sy0 + 1)

    # infer connector orientation relative to circle center.
    mean_x = sum(xs) / max(1, len(xs))
    mean_y = sum(ys) / max(1, len(ys))
    dx = abs(mean_x - cx)
    dy = abs(mean_y - cy)
    if dx >= dy:
        stem_direction = "right" if mean_x >= cx else "left"
    else:
        stem_direction = "bottom" if mean_y >= cy else "top"

    stem_values = [grayscale[element.y0 + y][element.x0 + x] for x, y in best_cluster]
    stem_color = _gray_to_hex(round(sum(stem_values) / max(1, len(stem_values))))

    fill_color, stroke_color, stroke_width = estimate_stroke_style(grayscale, element, candidate)

    stem_x = float(element.x0 + sx0)
    stem_y = float(element.y0 + sy0)
    stem_wf = float(stem_w)
    stem_hf = float(stem_h)
    overlap = max(0.6, float(stroke_width or 0.0) * 0.55)

    if stem_direction in {"bottom", "top"}:
        circle_cx = float(element.x0) + cx
        circle_cy = float(element.y0) + cy
        stem_x = circle_cx - (stem_wf / 2.0)
        old_bottom = float(element.y0 + sy1 + 1)
        old_top = float(element.y0 + sy0)
        if stem_direction == "bottom":
            stem_y = circle_cy + r - overlap
            stem_hf = max(1.0, old_bottom - stem_y)
        else:
            stem_y = old_top
            stem_hf = max(1.0, (circle_cy - r + overlap) - stem_y)
    else:
        circle_cx = float(element.x0) + cx
        circle_cy = float(element.y0) + cy
        stem_y = circle_cy - (stem_hf / 2.0)
        old_right = float(element.x0 + sx1 + 1)
        old_left = float(element.x0 + sx0)
        overlap_lr = min(0.2, overlap)
        if stem_direction == "right":
            stem_x = circle_cx + r - overlap_lr
            stem_wf = max(1.0, old_right - stem_x)
        else:
            stem_x = old_left
            stem_wf = max(1.0, (circle_cx - r + overlap_lr) - stem_x)
