"""Scalar clamp helper extracted from :mod:`src.image_composite_converter`."""

from __future__ import annotations


def clip_scalar(value: float, low: float, high: float) -> float:
    """Return value clamped to ``[low, high]`` with ``numpy.clip`` scalar semantics."""
    lo = float(low)
    hi = float(high)
    # Mirror numpy.clip behaviour for inverted bounds (a_min > a_max):
    # any scalar collapses to the supplied upper bound.
    if lo > hi:
        return hi
    v = float(value)
    if v < lo:
        return lo
    if v > hi:
        return hi
    return v
