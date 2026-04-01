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


def resolveOptionalDependencies():
    return cv2, np, fitz


def readRaster(path: Path):
    if cv2 is None:
        return None
    return cv2.imread(str(path), cv2.IMREAD_UNCHANGED)


def renderSvg(path: Path):
    if fitz is None or np is None:
        return None
    try:
        with fitz.open(str(path)) as doc:
            page = doc.load_page(0)
            pix = page.get_pixmap(alpha=True)
            arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
            return arr
    except Exception:
        return None


def readPreview(path: Path):
    if path.suffix.lower() in RASTER_EXTENSIONS:
        return readRaster(path)
    if path.suffix.lower() == ".svg":
        return renderSvg(path)
    return None


def createTiledOverviewImage(images: list, columns: int = 6, tile_size: int = 96):
    if np is None or cv2 is None or not images:
        return None
    rows = int(math.ceil(len(images) / max(1, columns)))
    canvas = np.full((rows * tile_size, columns * tile_size, 3), 255, dtype=np.uint8)
    for idx, img in enumerate(images):
        if img is None:
            continue
        row, col = divmod(idx, columns)
        tile = cv2.resize(img, (tile_size, tile_size), interpolation=cv2.INTER_AREA)
        if tile.ndim == 2:
            tile = cv2.cvtColor(tile, cv2.COLOR_GRAY2BGR)
        elif tile.shape[2] == 4:
            tile = cv2.cvtColor(tile, cv2.COLOR_BGRA2BGR)
        y0, x0 = row * tile_size, col * tile_size
        canvas[y0 : y0 + tile_size, x0 : x0 + tile_size] = tile
    return canvas


def readSvgText(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def extractSvgBounds(svg_text: str) -> tuple[float, float, float, float] | None:
    match = SVG_VIEWBOX_RE.search(svg_text)
    if not match:
        return None
    x, y, w, h = map(float, match.groups())
    return x, y, w, h


def extractSvgInner(svg_text: str) -> str:
    start = svg_text.find(">")
    end = svg_text.rfind("</svg>")
    if start < 0 or end < 0 or end <= start:
        return svg_text
    return svg_text[start + 1 : end]


def createTiledOverviewSvg(entries: list[tuple[str, str]], columns: int = 6, tile_size: int = 96) -> str:
    rows = int(math.ceil(len(entries) / max(1, columns)))
    width = columns * tile_size
    height = rows * tile_size
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#fff"/>',
    ]
    for idx, (label, inner_svg) in enumerate(entries):
        row, col = divmod(idx, columns)
        x, y = col * tile_size, row * tile_size
        parts.append(f'<g transform="translate({x},{y})">')
        parts.append(f'<title>{escape(label)}</title>')
        parts.append(inner_svg)
        parts.append("</g>")
    parts.append("</svg>")
    return "".join(parts)


def generateConversionOverviews(converted_dir: Path, output_path: Path | None = None) -> Path | None:
    converted_dir = Path(converted_dir)
    if output_path is None:
        output_path = converted_dir / "reports" / "overview_diff_tiles.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    image_paths = sorted(path for path in converted_dir.glob("*") if path.suffix.lower() in RASTER_EXTENSIONS)
    previews = [readPreview(path) for path in image_paths]
    tiled = createTiledOverviewImage(previews)
    if tiled is None:
        return None
    cv2.imwrite(str(output_path), tiled)
    return output_path


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
