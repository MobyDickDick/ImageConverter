"""Backward-compatible wrapper for the legacy camelCase module name."""

from __future__ import annotations

import src.image_composite_converter as _polish

for _name in dir(_polish):
    if _name.startswith("__"):
        continue
    globals()[_name] = getattr(_polish, _name)

main = _polish.main

if __name__ == "__main__":
    raise SystemExit(main())
