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
    if debug_ac0811_dir and str(base_name).upper() == "AC0811":
        debug_dir = os.path.join(debug_ac0811_dir, os.path.splitext(filename)[0])
        os.makedirs(debug_dir, exist_ok=True)
        return debug_dir
    return None


def buildNonCompositeGradientStripeValidationLogLinesImpl(
    *,
    semantic_mode_visual_override: bool,
    strategy_stop_count: int,
) -> list[str]:
    log_status = (
        "non_composite_gradient_stripe_visual_override"
        if semantic_mode_visual_override
        else "non_composite_gradient_stripe"
    )
    return [
        f"status={log_status}",
        f"strategy=gradient_stripe;stop_count={strategy_stop_count}",
    ]
