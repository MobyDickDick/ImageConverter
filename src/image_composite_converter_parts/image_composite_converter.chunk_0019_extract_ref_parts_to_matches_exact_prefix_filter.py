

def _extract_ref_parts(name: str) -> tuple[str, int] | None:
    match = re.match(r"^([A-Z]{2,3})(\d{3,4})$", name.upper())
    if not match:
        return None
    return match.group(1), int(match.group(2))


def _normalize_range_token(value: str) -> str:
    base = get_base_name_from_file(str(value or "").upper())
    return re.sub(r"[^A-Z0-9]", "", base)


def _compact_range_token(value: str) -> str:
    token = _normalize_range_token(value)
    match = re.match(r"^([A-Z]+)(\d+)$", token)
    if not match:
        return token
    letters, digits = match.groups()
    return f"{letters[0]}{digits}"


def _shared_partial_range_token(start_ref: str, end_ref: str) -> str:
    start_token = _normalize_range_token(start_ref)
    end_token = _normalize_range_token(end_ref)
    compact_start = _compact_range_token(start_ref)
    compact_end = _compact_range_token(end_ref)
    if not start_token or not end_token:
        return ""
    for left, right in ((start_token, end_token), (compact_start, compact_end)):
        if left and left == right:
            return left
        if left and left in right:
            return left
        if right and right in left:
            return right

        max_len = min(len(left), len(right))
        for length in range(max_len, 2, -1):
            for idx in range(0, len(left) - length + 1):
                candidate = left[idx: idx + length]
                if candidate in right:
                    return candidate
    return ""


def _matches_partial_range_token(filename: str, start_ref: str, end_ref: str) -> bool:
    token = _shared_partial_range_token(start_ref, end_ref)
    if not token:
        return False
    stem = _normalize_range_token(get_base_name_from_file(os.path.splitext(filename)[0]))
    if not stem:
        return False
    if token in stem:
        return True

    pos = 0
    for char in stem:
        if pos < len(token) and char == token[pos]:
            pos += 1
    return pos == len(token)


def _extract_symbol_family(name: str) -> str | None:
    """Extract 2-3 letter corpus family prefixes such as AC, GE, DLG, or NAV."""
    match = re.match(r"^([A-Z]{2,3})\d{3,4}$", str(name).upper())
    if not match:
        return None
    return match.group(1)


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


