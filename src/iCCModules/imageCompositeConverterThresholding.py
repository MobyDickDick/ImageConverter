"""Extracted thresholding and mask-overlap helpers for imageCompositeConverter."""

from __future__ import annotations


def computeOtsuThresholdImpl(grayscale: list[list[int]]) -> int:
    hist = [0] * 256
    total = 0
    for row in grayscale:
        for value in row:
            hist[value] += 1
            total += 1
    if total == 0:
        return 220
    sum_total = sum(i * hist[i] for i in range(256))
    sum_bg = 0.0
    weight_bg = 0
    max_var = -1.0
    threshold = 220
    for t in range(256):
        weight_bg += hist[t]
        if weight_bg == 0:
            continue
        weight_fg = total - weight_bg
        if weight_fg == 0:
            break
        sum_bg += t * hist[t]
        mean_bg = sum_bg / weight_bg
        mean_fg = (sum_total - sum_bg) / weight_fg
        between_var = weight_bg * weight_fg * (mean_bg - mean_fg) ** 2
        if between_var > max_var:
            max_var = between_var
            threshold = t
    return threshold


def adaptiveThresholdImpl(grayscale: list[list[int]], block_size: int = 15, c: int = 5) -> list[list[int]]:
    h = len(grayscale)
    w = len(grayscale[0]) if h else 0
    out = [[0] * w for _ in range(h)]
    radius = block_size // 2
    for y in range(h):
        for x in range(w):
            y0, y1 = max(0, y - radius), min(h, y + radius + 1)
            x0, x1 = max(0, x - radius), min(w, x + radius + 1)
            values = [grayscale[yy][xx] for yy in range(y0, y1) for xx in range(x0, x1)]
            thresh = (sum(values) / max(1, len(values))) - c
            out[y][x] = 1 if grayscale[y][x] < thresh else 0
    return out


def iouImpl(a: list[list[int]], b: list[list[int]]) -> float:
    inter = union = 0
    for y in range(len(a)):
        for x in range(len(a[0])):
            av, bv = a[y][x], b[y][x]
            if av and bv:
                inter += 1
            if av or bv:
                union += 1
    return inter / union if union else 0.0
