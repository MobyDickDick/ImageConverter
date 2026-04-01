import re

from ..normalizeRangeToken import normalizeRangeToken


def compactRangeToken(value: str) -> str:
    token = normalizeRangeToken(value)
    match = re.match(r"^([A-Z]+)(\d+)$", token)
    if not match:
        return token
    letters, digits = match.groups()
    return f"{letters[0]}{digits}"
