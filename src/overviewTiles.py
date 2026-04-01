"""Utilities for generating tiled overview images for converter outputs."""

from __future__ import annotations

import math
import sys
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


def _read_raster(path: Path):
    _resolve_optional_dependencies()
    if cv2 is None:
        return None
    img = cv2.imread(str(path), cv2.IMREAD_COLOR)
    return img


def _render_svg(path: Path):
    _resolve_optional_dependencies()
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


def _read_preview(path: Path):
    if path.suffix.lower() == ".svg":
        return _render_svg(path)
    if path.suffix.lower() in RASTER_EXTENSIONS:
        return _read_raster(path)
    return None


def create_tiled_overview_image(
    source_files: list[Path],
    output_path: Path,
    *,
    tile_size: int = 160,
    padding: int = 12,
    columns: int = 8,
) -> Path | None:
    """Create a labeled tile view from source files and write it to ``output_path``."""
    _resolve_optional_dependencies()
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
        preview = _read_preview(path)
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


def generate_conversion_overviews(
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
    diff_res = create_tiled_overview_image(diff_files, diff_out)
    if diff_res is not None:
        generated["diff"] = str(diff_res)

    svg_files = sorted(svg_root.glob("*.svg"))
    svg_out = reports_root / "overview_svg_tiles.png"
    svg_res = create_tiled_overview_image(svg_files, svg_out)
    if svg_res is not None:
        generated["svg"] = str(svg_res)

    return generated


def _resolve_optional_dependencies() -> None:
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
