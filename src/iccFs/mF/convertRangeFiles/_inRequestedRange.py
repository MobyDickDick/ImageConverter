import os

from ._inRequestedRangeFiles._extractRefParts import extractRefParts
from ._inRequestedRangeFiles._matchesExactPrefixFilter import matchesExactPrefixFilter
from ._inRequestedRangeFiles._matchesPartialRangeToken import matchesPartialRangeToken
from ._inRequestedRangeFiles.getBaseNameFromFile import getBaseNameFromFile


def inRequestedRange(filename: str, start_ref: str, end_ref: str) -> bool:
    stem = getBaseNameFromFile(os.path.splitext(filename)[0]).upper()
    current = extractRefParts(stem)
    start = extractRefParts(str(start_ref or "").upper())
    end = extractRefParts(str(end_ref or "").upper())

    if current and start and end and current[0] == start[0] == end[0]:
        low, high = sorted((start[1], end[1]))
        return low <= current[1] <= high

    if matchesExactPrefixFilter(filename, start_ref, end_ref):
        return True

    return matchesPartialRangeToken(filename, start_ref, end_ref)
