import os

from ._matchesExactPrefixFilterFiles.normalizeRangeToken import normalizeRangeToken
from ._matchesExactPrefixFilterFiles.getBaseNameFromFile import getBaseNameFromFile


def matchesExactPrefixFilter(filename: str, start_ref: str, end_ref: str) -> bool:
    start_token = normalizeRangeToken(start_ref)
    end_token = normalizeRangeToken(end_ref)
    if not start_token or start_token != end_token:
        return False
    stem = normalizeRangeToken(getBaseNameFromFile(os.path.splitext(filename)[0]))
    if not stem:
        return False
    return stem.startswith(start_token)
