def semanticTransferRotations(target_params: dict[str, object], donor_params: dict[str, object]) -> tuple[int, ...]:
    """Rotation candidates for semantic transfer while preserving symbol semantics."""
    has_text = bool(target_params.get("draw_text", False) or donor_params.get("draw_text", False))
    has_connector = bool(
        target_params.get("arm_enabled", False)
        or target_params.get("stem_enabled", False)
        or donor_params.get("arm_enabled", False)
        or donor_params.get("stem_enabled", False)
    )
    if has_text or has_connector:
        # Directional semantic badges (e.g. AC0812 left arm) encode orientation in
        # geometry. Rotating donor templates can improve pixel error but flips the
        # meaning of connector-side symbols. Keep transfer upright/unrotated.
        return (0,)
    return (0, 90, 180, 270)
