def _connector_arm_direction(params: dict[str, object]) -> int | None:
    """Return horizontal arm side: -1 left of circle, +1 right, or None if unknown."""
    x1 = params.get("arm_x1")
    x2 = params.get("arm_x2")
    cx = params.get("cx")
    if x1 is not None and x2 is not None and cx is not None:
        mid = (float(x1) + float(x2)) * 0.5
        delta = mid - float(cx)
        if abs(delta) > 1e-3:
            return -1 if delta < 0.0 else 1

    if x1 is not None and cx is not None:
        delta = float(x1) - float(cx)
        if abs(delta) > 1e-3:
            return -1 if delta < 0.0 else 1
    return None


def _connector_stem_direction(params: dict[str, object]) -> int | None:
    """Return vertical stem direction: -1 up, +1 down, or None if unknown."""
    y1 = params.get("arm_y1")
    y2 = params.get("arm_y2")
    if y1 is not None and y2 is not None:
        dy = float(y2) - float(y1)
        if abs(dy) > 1e-3:
            return -1 if dy < 0.0 else 1

    cy = params.get("cy")
    if y1 is not None and y2 is not None and cy is not None:
        mid = (float(y1) + float(y2)) * 0.5
        delta = mid - float(cy)
        if abs(delta) > 1e-3:
            return -1 if delta < 0.0 else 1
    return None


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

