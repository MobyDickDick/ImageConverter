"""Utilities for generating tiled overview images for converter outputs."""

from __future__ import annotations

import math
import os
import sys
import binascii
import struct
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


def _readRaster(path: Path):
    _resolveOptionalDependencies()
    if cv2 is None:
        return None
    img = _readRasterWithoutStderrNoise(path)
    return img


def _readRasterWithoutStderrNoise(path: Path):
    """Read raster input while suppressing noisy decoder stderr output."""
    if path.suffix.lower() == ".png" and not _hasValidPngStructure(path):
        return None

    stderr = sys.stderr
    fileno = getattr(stderr, "fileno", None)
    if fileno is None:
        return cv2.imread(str(path), cv2.IMREAD_COLOR)
    try:
        stderr_fd = fileno()
    except (OSError, ValueError):
        return cv2.imread(str(path), cv2.IMREAD_COLOR)

    saved_fd = os.dup(stderr_fd)
    try:
        with open(os.devnull, "w", encoding="utf-8") as devnull:
            os.dup2(devnull.fileno(), stderr_fd)
            return cv2.imread(str(path), cv2.IMREAD_COLOR)
    finally:
        os.dup2(saved_fd, stderr_fd)
        os.close(saved_fd)


def _hasValidPngStructure(path: Path) -> bool:
    try:
        payload = path.read_bytes()
    except OSError:
        return False

    if not payload.startswith(b"\x89PNG\r\n\x1a\n"):
        return False

    cursor = 8
    payload_len = len(payload)
    while cursor + 12 <= payload_len:
        chunk_len = struct.unpack(">I", payload[cursor : cursor + 4])[0]
        chunk_type = payload[cursor + 4 : cursor + 8]
        chunk_data_end = cursor + 8 + chunk_len
        chunk_crc_end = chunk_data_end + 4
        if chunk_crc_end > payload_len:
            return False
        chunk_data = payload[cursor + 8 : chunk_data_end]
        expected_crc = struct.unpack(">I", payload[chunk_data_end:chunk_crc_end])[0]
        actual_crc = binascii.crc32(chunk_type + chunk_data) & 0xFFFFFFFF
        if actual_crc != expected_crc:
            return False
        cursor = chunk_crc_end
        if chunk_type == b"IEND":
            return cursor == payload_len
    return False


def _renderSvg(path: Path):
    _resolveOptionalDependencies()
    if np is None or fitz is None:
        return None
    try:
        svg_text = path.read_text(encoding="utf-8")
        with fitz.open("pdf", svg_text.encode("utf-8")) as doc:
            pix = doc[0].get_pixmap(alpha=False)
    except Exception:
        return None
    arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    if pix.n == 4:
        return cv2.cvtColor(arr, cv2.COLOR_RGBA2BGR) if cv2 is not None else arr[:, :, :3]
    if pix.n == 3:
        return cv2.cvtColor(arr, cv2.COLOR_RGB2BGR) if cv2 is not None else arr
    return None


def _readPreview(path: Path):
    if path.suffix.lower() == ".svg":
        return _renderSvg(path)
    if path.suffix.lower() in RASTER_EXTENSIONS:
        return _readRaster(path)
    return None


def createTiledOverviewImage(
    source_files: list[Path],
    output_path: Path,
    *,
    tile_size: int = 160,
    padding: int = 12,
    columns: int = 8,
) -> Path | None:
    """Create a labeled tile view from source files and write it to ``output_path``."""
    _resolveOptionalDependencies()
    if cv2 is None or np is None:
        return None

    valid = [path for path in source_files if path.exists()]
    if not valid:
        return None

    cell_w = max(64, int(tile_size))
    label_h = 24
    cell_h = cell_w + label_h
    cols = max(1, int(columns))
    rows = int(math.ceil(len(valid) / cols))

    canvas_h = padding + rows * (cell_h + padding)
    canvas_w = padding + cols * (cell_w + padding)
    canvas = np.full((canvas_h, canvas_w, 3), 248, dtype=np.uint8)

    for idx, path in enumerate(valid):
        preview = _readPreview(path)
        if preview is None:
            continue

        if preview.ndim != 3:
            continue
        ph, pw = preview.shape[:2]
        if ph <= 0 or pw <= 0:
            continue

        scale = min(cell_w / pw, cell_w / ph)
        new_w = max(1, int(round(pw * scale)))
        new_h = max(1, int(round(ph * scale)))
        thumb = cv2.resize(preview, (new_w, new_h), interpolation=cv2.INTER_AREA)

        row = idx // cols
        col = idx % cols
        x0 = padding + col * (cell_w + padding)
        y0 = padding + row * (cell_h + padding)

        px = x0 + (cell_w - new_w) // 2
        py = y0 + (cell_w - new_h) // 2
        canvas[py : py + new_h, px : px + new_w] = thumb

        cv2.rectangle(canvas, (x0, y0), (x0 + cell_w, y0 + cell_w), (208, 208, 208), 1)
        label = path.stem
        cv2.putText(
            canvas,
            label,
            (x0 + 2, y0 + cell_w + 16),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.36,
            (45, 45, 45),
            1,
            cv2.LINE_AA,
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output_path), canvas)
    return output_path


def generateConversionOverviews(
    diff_dir: str | Path,
    svg_dir: str | Path,
    reports_dir: str | Path,
) -> dict[str, str]:
    """Generate standard converter overview tiles and return generated paths."""
    diff_root = Path(diff_dir)
    svg_root = Path(svg_dir)
    reports_root = Path(reports_dir)

    generated: dict[str, str] = {}

    diff_files = sorted(diff_root.glob("*_diff.png"))
    diff_out = reports_root / "overview_diff_tiles.png"
    diff_res = createTiledOverviewImage(diff_files, diff_out)
    if diff_res is not None:
        generated["diff"] = str(diff_res)

    svg_files = sorted(svg_root.glob("*.svg"))
    svg_out = reports_root / "overview_svg_tiles.png"
    svg_res = createTiledOverviewImage(svg_files, svg_out)
    if svg_res is not None:
        generated["svg"] = str(svg_res)

    return generated


def _resolveOptionalDependencies() -> None:
    """Try to reuse optional deps loaded by ``src.imageCompositeConverter``."""
    global cv2, np, fitz
    if cv2 is not None and np is not None and fitz is not None:
        return
    converter = sys.modules.get("src.imageCompositeConverter")
    if converter is None:
        return
    if cv2 is None:
        cv2 = getattr(converter, "cv2", None)
    if np is None:
        np = getattr(converter, "np", None)
    if fitz is None:
        fitz = getattr(converter, "fitz", None)
