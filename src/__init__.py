"""Top-level package for ImageConverter source modules.

Provides compatibility imports for Polish-notation (lower-camel) module names.
"""

from __future__ import annotations

from importlib import import_module
from types import ModuleType

__all__ = [
    "imageCompositeConverter",
    "overviewTiles",
]


def __getattr__(name: str) -> ModuleType:
    if name == "imageCompositeConverter":
        module = import_module(".imageCompositeConverter", __name__)
        globals()[name] = module
        return module
    if name == "overviewTiles":
        module = import_module(".overviewTiles", __name__)
        globals()[name] = module
        return module
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
