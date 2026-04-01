def iterationStrategyForPass(pass_index: int, base_iterations: int) -> tuple[int, int]:
    """Return (iteration_budget, badge_validation_rounds) for a quality pass."""
    p = max(0, int(pass_index))
    base = max(1, int(base_iterations))
    if p == 0:
        return base, 6
    if p == 1:
        return int(round(base * 1.2)), 7
    if p == 2:
        return int(round(base * 1.35)), 8
    return int(round(base * 1.5)), 8
