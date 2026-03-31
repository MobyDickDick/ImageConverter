"""Backward-compatible snake_case wrapper for ``syncCoreOverrides``."""

from __future__ import annotations

import src.iccFs.syncCoreOverrides as _legacy

for _name, _value in _legacy.__dict__.items():
    if _name.startswith("__"):
        continue
    globals()[_name] = _value
