"""Top-level package for ImageConverter source modules.

Provides compatibility imports for both snake_case and Polish-notation
(lower-camel) module naming.
"""

from __future__ import annotations

from importlib import import_module
from types import ModuleType

__all__ = [
    "imageCompositeConverter",
    "overviewTiles",
    "overview_tiles",
]


def __getattr__(name: str) -> ModuleType:
    if name == "imageCompositeConverter":
        module = import_module(".imageCompositeConverter", __name__)
        globals()[name] = module
        return module
    if name in {"overviewTiles", "overview_tiles"}:
        module = import_module(".overviewTiles", __name__)
        globals()["overviewTiles"] = module
        globals()["overview_tiles"] = module
        return module
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
