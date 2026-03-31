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
