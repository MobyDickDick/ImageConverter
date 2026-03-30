from src import image_composite_converter as _icc

globals().update(vars(_icc))

def _mask_bbox(mask: np.ndarray) -> tuple[float, float, float, float] | None:
    """Return (xmin, ymin, xmax, ymax) for truthy mask pixels."""
    if mask is None:
        return None
    m = np.asarray(mask).astype(bool)
    if m.size == 0 or not m.any():
        return None
    ys, xs = np.nonzero(m)
    return float(xs.min()), float(ys.min()), float(xs.max()), float(ys.max())
