"""Top-level package for ImageConverter source modules.

Provides compatibility imports for both snake_case and Polish-notation
(lower-camel) module naming.
"""

from . import imageCompositeConverter
from . import image_composite_converter
from . import overviewTiles
overview_tiles = overviewTiles

__all__ = [
    "imageCompositeConverter",
    "image_composite_converter",
    "overviewTiles",
    "overview_tiles",
]
