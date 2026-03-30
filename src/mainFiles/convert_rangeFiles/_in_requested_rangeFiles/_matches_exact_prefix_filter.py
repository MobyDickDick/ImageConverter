from src import image_composite_converter as _icc

globals().update(vars(_icc))

def _matches_exact_prefix_filter(filename: str, start_ref: str, end_ref: str) -> bool:
    start_token = _normalize_range_token(start_ref)
    end_token = _normalize_range_token(end_ref)
    if not start_token or start_token != end_token:
        return False
    # Three-digit bounds like AC080 are typically used as shorthand for the
    # exact AC0800 family (L/M/S). They should not fan out to AC0801, AC0802,
    # ... which can unexpectedly multiply batch size.
    if re.fullmatch(r"[A-Z]{2,3}\d{3}", start_token) and start_token.endswith("0"):
        start_token = f"{start_token}0"

    stem = _normalize_range_token(get_base_name_from_file(os.path.splitext(filename)[0]))
    if not stem:
        return False
    if not stem.startswith(start_token):
        return False
    if len(stem) == len(start_token):
        return True
    return stem[len(start_token)].isdigit()
