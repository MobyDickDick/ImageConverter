"""Mask overlap metrics for primitive element scoring."""

from __future__ import annotations


def iouImpl(a: list[list[int]], b: list[list[int]]) -> float:
    inter = union = 0
    for y in range(len(a)):
        row_a = a[y]
        row_b = b[y]
        for x in range(len(row_a)):
            av = row_a[x]
            bv = row_b[x]
            if av and bv:
                inter += 1
            if av or bv:
                union += 1
    return inter / union if union else 0.0
