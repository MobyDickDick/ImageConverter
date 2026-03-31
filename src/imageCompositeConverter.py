"""Backward-compatible camelCase wrapper for ``image_composite_converter``."""

from __future__ import annotations

import src.image_composite_converter as _modern

for _name in dir(_modern):
    if _name.startswith("__"):
        continue
    try:
        globals()[_name] = getattr(_modern, _name)
    except AttributeError:
        continue
