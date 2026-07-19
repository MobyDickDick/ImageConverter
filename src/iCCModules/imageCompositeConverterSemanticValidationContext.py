from __future__ import annotations

import os


def resolveSemanticValidationDebugDirImpl(
    *,
    debug_element_diff_dir: str | None,
    debug_ac0811_dir: str | None,
    filename: str,
    base_name: str,
) -> str | None:
    if debug_element_diff_dir:
        debug_dir = os.path.join(debug_element_diff_dir, os.path.splitext(filename)[0])
        os.makedirs(debug_dir, exist_ok=True)
        return debug_dir
    if debug_ac0811_dir:
        debug_dir = os.path.join(debug_ac0811_dir, os.path.splitext(filename)[0])
        os.makedirs(debug_dir, exist_ok=True)
        return debug_dir
    return None


def buildNonCompositeGradientStripeValidationLogLinesImpl(
    *,
    semantic_mode_visual_override: bool,
    strategy_stop_count: int,
) -> list[str]:
    return [
        "status=non_composite_smooth_gradient_strategy_disabled",
        "strategy=smooth_gradient;legacy_stop_count_ignored=1",
    ]
