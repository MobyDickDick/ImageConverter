import re

from .._normalizeRangeToken import _normalizeRangeToken


def _compactRangeToken(value: str) -> str:
    token = _normalizeRangeToken(value)
    match = re.match(r"^([A-Z]+)(\d+)$", token)
    if not match:
        return token
    letters, digits = match.groups()
    return f"{letters[0]}{digits}"
