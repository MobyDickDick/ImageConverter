def _rank_template_transfer_donors(
    target_row: dict[str, object],
    donor_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    """Prioritize donors that are already good and geometrically close to target."""
    target_base = str(target_row.get("base", "")).upper()
    target_sig: dict[str, float] | None = None
    target_params = target_row.get("params")
    if isinstance(target_params, dict):
        target_sig = _normalized_geometry_signature(
            int(target_row.get("w", 0)),
            int(target_row.get("h", 0)),
            dict(target_params),
        )

    ranked: list[tuple[tuple[float, float, float], dict[str, object]]] = []
    for donor in donor_rows:
        donor_base = str(donor.get("base", "")).upper()
        donor_error_pp = float(donor.get("error_per_pixel", float("inf")))
        donor_sig: dict[str, float] | None = None
        donor_params = donor.get("params")
        if isinstance(donor_params, dict):
            donor_sig = _normalized_geometry_signature(int(donor.get("w", 0)), int(donor.get("h", 0)), dict(donor_params))

        delta = float("inf")
        if target_sig is not None and donor_sig is not None:
            delta = _max_signature_delta(target_sig, donor_sig)

        key = (0.0 if donor_base == target_base else 1.0, delta, donor_error_pp)
        ranked.append((key, donor))

    ranked.sort(key=lambda item: item[0])
    return [donor for _, donor in ranked]


def _template_transfer_donor_family_compatible(
    target_base: str,
    donor_base: str,
    *,
    documented_alias_refs: set[str] | None = None,
) -> bool:
    """Allow fallback transfer within family, plus documented cross-family aliases."""
    alias_refs = {str(v).upper() for v in (documented_alias_refs or set()) if str(v).strip()}
    if donor_base.upper() in alias_refs:
        return True

    target_family = _extract_symbol_family(target_base)
    donor_family = _extract_symbol_family(donor_base)
    if target_family is None or donor_family is None:
        # Keep legacy behavior for non-standard names where family extraction fails.
        return True
    return target_family == donor_family




def _semantic_transfer_rotations(target_params: dict[str, object], donor_params: dict[str, object]) -> tuple[int, ...]:
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


