def _connectorStemDirection(params: dict[str, object]) -> int | None:
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
