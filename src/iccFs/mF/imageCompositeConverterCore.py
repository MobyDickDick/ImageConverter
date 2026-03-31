"""Polish-notation alias module for ``image_composite_converter_core``.

This module now exposes **both** the original symbol names and generated
Polish-notation aliases (prefix style via lower-camel identifiers) for all
callables from ``image_composite_converter_core``.
"""

from __future__ import annotations

import src.iccFs.mF.image_composite_converter_core as _legacy


def _to_polish_notation(name: str) -> str:
    """Convert ``snake_case`` names to lower-camel Polish-notation aliases."""
    if "_" not in name:
        return name
    parts = [part for part in name.split("_") if part]
    if not parts:
        return name
    return parts[0].lower() + "".join(part[:1].upper() + part[1:] for part in parts[1:])


for _name in dir(_legacy):
    if _name.startswith("__"):
        continue
    _value = getattr(_legacy, _name)
    globals()[_name] = _value
    if callable(_value):
        _pn_name = _to_polish_notation(_name)
        if _pn_name and _pn_name not in globals():
            globals()[_pn_name] = _value
