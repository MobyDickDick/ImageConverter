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
