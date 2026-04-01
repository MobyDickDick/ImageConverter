import re

from .getBaseNameFromFile import getBaseNameFromFile


def normalizeRangeToken(value: str) -> str:
    base = getBaseNameFromFile(str(value or "").upper())
    return re.sub(r"[^A-Z0-9]", "", base)
