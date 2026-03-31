"""Backward-compatible snake_case wrapper for ``successfulConversions``.

Re-export all public and private names so internal imports that rely on
underscore-prefixed helpers keep working.
"""

from __future__ import annotations

import src.successfulConversions as _legacy

for _name, _value in _legacy.__dict__.items():
    if _name.startswith("__"):
        continue
    globals()[_name] = _value
