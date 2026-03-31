"""Snake-case compatibility wrapper for overview tile helpers."""

from __future__ import annotations

import src.iccFs.mF.overviewTiles as _polish

for _name in dir(_polish):
    if _name.startswith("__"):
        continue
    globals()[_name] = getattr(_polish, _name)
