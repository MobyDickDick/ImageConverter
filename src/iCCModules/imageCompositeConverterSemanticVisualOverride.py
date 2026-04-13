from __future__ import annotations

import copy
from typing import Callable


def applySemanticVisualOverrideImpl(
    *,
    params: dict[str, object],
    stripe_strategy: object,
    elongated_rect_geometry: object,
    print_fn: Callable[[str], None],
) -> tuple[dict[str, object], bool]:
    semantic_mode_visual_override = params.get("mode") == "semantic_badge" and (
        stripe_strategy is not None or elongated_rect_geometry
    )
    if not semantic_mode_visual_override:
        return params, False

    updated_params = copy.deepcopy(params)
    updated_params["mode"] = "non_composite_visual_override"
    updated_params["visual_override_reason"] = (
        "gradient_stripe_geometry_detected"
        if stripe_strategy is not None
        else "elongated_rect_geometry_detected"
    )
    print_fn(
        "  -> Geometrie-Override: Semantik deutet auf Badge, "
        "Bildinhalt ist jedoch eine längliche rechteckige Geometrie."
    )
    return updated_params, True
