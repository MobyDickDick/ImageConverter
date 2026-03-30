def _matches_exact_prefix_filter(filename: str, start_ref: str, end_ref: str) -> bool:
    start_token = _normalize_range_token(start_ref)
    end_token = _normalize_range_token(end_ref)
    if not start_token or start_token != end_token:
        return False
    stem = _normalize_range_token(get_base_name_from_file(os.path.splitext(filename)[0]))
    if not stem:
        return False
    match = re.match(r"^([A-Z]{2,3})(\d{3})$", start_token)
    if match and match.group(2).endswith("0"):
        return stem == f"{match.group(1)}{match.group(2)}0"
    return stem.startswith(start_token)
