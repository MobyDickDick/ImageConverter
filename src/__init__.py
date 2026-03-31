"""Top-level package for ImageConverter source modules.

Provides compatibility imports for both snake_case and Polish-notation
(lower-camel) module naming.
"""

from . import imageCompositeConverter
from . import overviewTiles
overview_tiles = overviewTiles

__all__ = [
    "imageCompositeConverter",
    "overviewTiles",
    "overview_tiles",
]
