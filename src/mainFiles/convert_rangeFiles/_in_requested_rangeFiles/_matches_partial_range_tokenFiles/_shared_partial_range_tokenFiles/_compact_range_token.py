from src import image_composite_converter as _icc

globals().update(vars(_icc))

def _compact_range_token(value: str) -> str:
    token = _normalize_range_token(value)
    match = re.match(r"^([A-Z]+)(\d+)$", token)
    if not match:
        return token
    letters, digits = match.groups()
    return f"{letters[0]}{digits}"
