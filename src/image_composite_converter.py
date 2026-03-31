"""Snake-case compatibility wrapper for ``src.imageCompositeConverter``."""

from __future__ import annotations

import re

import src.imageCompositeConverter as _polish


_CAMEL_BOUNDARY_RE = re.compile(r"(?<!^)(?=[A-Z])")


def _camel_to_snake(name: str) -> str:
    leading = ""
    while name.startswith("_"):
        leading += "_"
        name = name[1:]
    if not name:
        return leading
    return leading + _CAMEL_BOUNDARY_RE.sub("_", name).lower()


for _name in dir(_polish):
    if _name.startswith("__"):
        continue
    _value = getattr(_polish, _name)
    globals()[_name] = _value
    if callable(_value):
        _snake_name = _camel_to_snake(_name)
        if _snake_name and _snake_name not in globals():
            globals()[_snake_name] = _value
