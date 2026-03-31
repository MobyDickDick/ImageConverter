def _matchesPartialRangeToken(filename: str, start_ref: str, end_ref: str) -> bool:
    token = _sharedPartialRangeToken(start_ref, end_ref)
    if not token:
        return False
    stem = _normalizeRangeToken(getBaseNameFromFile(os.path.splitext(filename)[0]))
    if not stem:
        return False
    if token in stem:
        return True

    pos = 0
    for char in stem:
        if pos < len(token) and char == token[pos]:
            pos += 1
    return pos == len(token)
