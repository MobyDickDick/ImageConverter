"""Compatibility alias for legacy snake_case imports.

The primary CLI/module entrypoint is ``src.imageCompositeConverter``.
This shim keeps ``import src.image_composite_converter`` functional.
"""

from __future__ import annotations

import src.imageCompositeConverter as _legacy

for _name in dir(_legacy):
    if _name.startswith("__"):
        continue
    try:
        globals()[_name] = getattr(_legacy, _name)
    except AttributeError:
        continue
