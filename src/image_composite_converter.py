"""Backward-compatible wrapper for the Polish-notation module name.

New code should import ``src.imageCompositeConverter``.
"""

from __future__ import annotations

import src.imageCompositeConverter as _polish

for _name in dir(_polish):
    if _name.startswith("__"):
        continue
    globals()[_name] = getattr(_polish, _name)

main = _polish.main

if __name__ == "__main__":
    raise SystemExit(main())
