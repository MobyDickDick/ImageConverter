"""Utilities for generating tiled overview images for converter outputs."""

from __future__ import annotations

import math
import re
import sys
from html import escape
from pathlib import Path
from typing import Callable

try:
    import cv2  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    cv2 = None

try:
    import numpy as np  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    np = None

try:
    import fitz  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    fitz = None

ImagePredicate = Callable[[Path], bool]


RASTER_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".gif"}
SVG_VIEWBOX_RE = re.compile(
    r'viewBox\s*=\s*["\']\s*([+-]?\d*\.?\d+)\s+([+-]?\d*\.?\d+)\s+([+-]?\d*\.?\d+)\s+([+-]?\d*\.?\d+)\s*["\']',
    flags=re.IGNORECASE,
)






















# Backward-compatible aliases
readRaster = readRaster
renderSvg = renderSvg
readPreview = readPreview
createTiledOverviewImage = createTiledOverviewImage
readSvgText = readSvgText
extractSvgBounds = extractSvgBounds
extractSvgInner = extractSvgInner
createTiledOverviewSvg = createTiledOverviewSvg
generateConversionOverviews = generateConversionOverviews
resolveOptionalDependencies = resolveOptionalDependencies
