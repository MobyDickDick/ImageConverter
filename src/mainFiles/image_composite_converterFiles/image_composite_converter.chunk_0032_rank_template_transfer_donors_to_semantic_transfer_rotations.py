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
""" End move to File mainFiles/convert_rangeFiles/_try_template_transferFiles/_rank_template_transfer_donors.py """


""" Start move to File mainFiles/convert_rangeFiles/_try_template_transferFiles/_template_transfer_donor_family_compatible.py
import src
"""
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
""" End move to File mainFiles/convert_rangeFiles/_try_template_transferFiles/_template_transfer_donor_family_compatible.py """




""" Start move to File mainFiles/convert_rangeFiles/_try_template_transferFiles/_semantic_transfer_rotations.py
import src
"""
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
""" End move to File mainFiles/convert_rangeFiles/_try_template_transferFiles/_semantic_transfer_rotations.py """






""" Start move to File mainFiles/convert_rangeFiles/_try_template_transferFiles/_semantic_transfer_is_compatible.py
import src
"""
