"""Perception geometry helpers extracted from imageCompositeConverterRemaining."""

from __future__ import annotations


def looksLikeElongatedForegroundRectImpl(
    img,
    *,
    np_module,
    white_threshold: int = 245,
) -> bool:
    if img is None or np_module is None:
        return False
    h, w = img.shape[:2]
    if h <= 0 or w <= 0:
        return False
    mask = (img < int(white_threshold)).any(axis=2)
    ys, xs = np_module.where(mask)
    if len(xs) == 0 or len(ys) == 0:
        return False
    x0 = int(xs.min())
    x1 = int(xs.max())
    y0 = int(ys.min())
    y1 = int(ys.max())
    bw = x1 - x0 + 1
    bh = y1 - y0 + 1
    if bw <= 0 or bh <= 0:
        return False
    aspect = float(max(bw, bh)) / max(1.0, float(min(bw, bh)))
    fill_ratio = float(np_module.count_nonzero(mask[y0 : y1 + 1, x0 : x1 + 1])) / float(max(1, bw * bh))
    return bool(aspect >= 3.2 and fill_ratio >= 0.45)
