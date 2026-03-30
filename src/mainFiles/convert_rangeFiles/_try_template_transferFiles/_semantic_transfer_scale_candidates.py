from src import image_composite_converter as _icc

globals().update(vars(_icc))

def _semantic_transfer_scale_candidates(base_scale: float) -> list[float]:
    """Broader scale ladder for semantic badge transfer exploration."""
    core = _template_transfer_scale_candidates(base_scale)
    extra = [0.55, 0.65, 0.75, 0.85, 1.00, 1.15, 1.30, 1.50, 1.75, 2.00]
    values = []
    seen: set[float] = set()
    for v in [*core, *extra]:
        value = float(min(2.2, max(0.5, float(v))))
        key = round(value, 4)
        if key in seen:
            continue
        seen.add(key)
        values.append(key)
    return values
