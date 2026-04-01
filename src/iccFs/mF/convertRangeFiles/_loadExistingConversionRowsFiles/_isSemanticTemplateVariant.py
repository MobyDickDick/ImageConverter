def isSemanticTemplateVariant(base_name: str, params: dict[str, object] | None = None) -> bool:
    """Return whether an existing converted SVG should participate as semantic donor."""
    normalized = str(getBaseNameFromFile(base_name or "")).upper()
    if not normalized:
        return False
    if normalized.startswith("AC08") or normalized in {"AR0100"}:
        return True
    if isinstance(params, dict) and str(params.get("mode", "")).lower() == "semantic_badge":
        return True
    return False
