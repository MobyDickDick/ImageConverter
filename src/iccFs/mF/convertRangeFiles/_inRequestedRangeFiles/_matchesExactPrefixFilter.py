import os

from ._matchesExactPrefixFilterFiles._normalizeRangeToken import _normalizeRangeToken
from ._matchesExactPrefixFilterFiles.getBaseNameFromFile import getBaseNameFromFile


def _matchesExactPrefixFilter(filename: str, start_ref: str, end_ref: str) -> bool:
    start_token = _normalizeRangeToken(start_ref)
    end_token = _normalizeRangeToken(end_ref)
    if not start_token or start_token != end_token:
        return False
    stem = _normalizeRangeToken(getBaseNameFromFile(os.path.splitext(filename)[0]))
    if not stem:
        return False
    return stem.startswith(start_token)
