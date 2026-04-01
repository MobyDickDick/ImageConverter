import os

from ._matchesPartialRangeTokenFiles._normalizeRangeToken import normalizeRangeToken
from ._matchesPartialRangeTokenFiles._sharedPartialRangeToken import sharedPartialRangeToken
from ._matchesPartialRangeTokenFiles.getBaseNameFromFile import getBaseNameFromFile


def matchesPartialRangeToken(filename: str, start_ref: str, end_ref: str) -> bool:
    stem = os.path.splitext(filename)[0]
    stem_token = normalizeRangeToken(getBaseNameFromFile(stem))
    shared = sharedPartialRangeToken(start_ref, end_ref)
    return bool(stem_token and shared and shared in stem_token)
