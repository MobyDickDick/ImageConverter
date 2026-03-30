from src import image_composite_converter as _icc

globals().update(vars(_icc))

def _iteration_strategy_for_pass(pass_idx: int, base_iterations: int) -> tuple[int, int]:
    """Adaptive per-pass search budget for unresolved quality cases."""
    p = max(1, int(pass_idx))
    base = max(1, int(base_iterations))
    phase = (p - 1) % 3

    if phase == 0:
        return base + p, 6 + p
    if phase == 1:
        return base + 24 + (p * 2), 7 + p
    return base + 48 + (p * 3), 8 + p
