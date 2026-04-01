import os

from ._matchesExactPrefixFilterFiles._normalizeRangeToken import normalizeRangeToken
from ._matchesExactPrefixFilterFiles.getBaseNameFromFile import getBaseNameFromFile


def matchesExactPrefixFilter(filename: str, start_ref: str, end_ref: str) -> bool:
    """Allow filtering by explicit shared non-numeric prefixes (e.g. AC08*)."""
    stem = os.path.splitext(filename)[0]
    stem_token = normalizeRangeToken(getBaseNameFromFile(stem))
    start_token = normalizeRangeToken(start_ref)
    end_token = normalizeRangeToken(end_ref)
    if not stem_token or not start_token or not end_token:
        return False
    if start_token == end_token:
        return stem_token.startswith(start_token)
    return False
