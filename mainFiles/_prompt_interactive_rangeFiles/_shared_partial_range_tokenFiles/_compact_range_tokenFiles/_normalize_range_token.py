def _normalize_range_token(value: str) -> str:
    base = get_base_name_from_file(str(value or "").upper())
    return re.sub(r"[^A-Z0-9]", "", base)
