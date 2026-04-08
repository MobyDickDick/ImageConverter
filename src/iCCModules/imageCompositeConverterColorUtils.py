"""Color/scalar helper utilities extracted from the converter monolith."""

from __future__ import annotations


def clipImpl(value, low, high, *, np_module, clip_scalar_fn):
    """Clip scalar/array values while keeping numpy optional for scalars."""
    if np_module is not None:
        return np_module.clip(value, low, high)
    if isinstance(value, (int, float)):
        return clip_scalar_fn(float(value), float(low), float(high))
    raise RuntimeError("numpy is required for non-scalar clip operations")


def grayToHexImpl(v: float) -> str:
    g = max(0, min(255, int(round(v))))
    return f"#{g:02x}{g:02x}{g:02x}"
