def _semantic_transfer_is_compatible(target_params: dict[str, object], donor_params: dict[str, object]) -> bool:
    """Return whether donor semantics can preserve target semantic geometry."""
    target_has_arm = bool(target_params.get("arm_enabled", False))
    target_has_stem = bool(target_params.get("stem_enabled", False))
    donor_has_arm = bool(donor_params.get("arm_enabled", False))
    donor_has_stem = bool(donor_params.get("stem_enabled", False))

    # Keep connector type stable for directional symbols (arm vs stem).
    if target_has_arm != donor_has_arm:
        return False
    if target_has_stem != donor_has_stem:
        return False

    target_has_text = bool(target_params.get("draw_text", False))
    donor_has_text = bool(donor_params.get("draw_text", False))
    if target_has_text != donor_has_text:
        return False

    # If both carry labels, require same text mode (e.g. VOC vs CO₂ path families).
    if target_has_text and donor_has_text:
        target_mode = str(target_params.get("text_mode", "")).lower()
        donor_mode = str(donor_params.get("text_mode", "")).lower()
        if target_mode and donor_mode and target_mode != donor_mode:
            return False

    # Directional connector families (e.g. AC0810 right arm vs AC0812 left arm)
    # must keep side/orientation stable during semantic transfer.
    if target_has_arm and donor_has_arm:
        target_arm_dir = _connector_arm_direction(target_params)
        donor_arm_dir = _connector_arm_direction(donor_params)
        if target_arm_dir is not None and donor_arm_dir is not None and target_arm_dir != donor_arm_dir:
            return False

    if target_has_stem and donor_has_stem:
        target_stem_dir = _connector_stem_direction(target_params)
        donor_stem_dir = _connector_stem_direction(donor_params)
        if target_stem_dir is not None and donor_stem_dir is not None and target_stem_dir != donor_stem_dir:
            return False

    return True
""" End move to File mainFiles/convert_rangeFiles/_try_template_transferFiles/_semantic_transfer_is_compatible.py """


""" Start move to File mainFiles/convert_rangeFiles/_try_template_transferFiles/_semantic_transfer_is_compatibleFiles/_connector_arm_direction.py
import src
"""
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
""" End move to File mainFiles/convert_rangeFiles/_try_template_transferFiles/_semantic_transfer_is_compatibleFiles/_connector_arm_direction.py """


""" Start move to File mainFiles/convert_rangeFiles/_try_template_transferFiles/_semantic_transfer_is_compatibleFiles/_connector_stem_direction.py
import src
"""
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
""" End move to File mainFiles/convert_rangeFiles/_try_template_transferFiles/_semantic_transfer_is_compatibleFiles/_connector_stem_direction.py """


""" Start move to File mainFiles/convert_rangeFiles/_try_template_transferFiles/_semantic_transfer_scale_candidates.py
import src
"""
