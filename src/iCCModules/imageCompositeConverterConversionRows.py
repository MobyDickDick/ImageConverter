"""Conversion-row loading helpers extracted from imageCompositeConverter."""

from __future__ import annotations

import csv
import math
import os
import struct
from pathlib import Path
from typing import Callable


DefReadSvgGeometry = Callable[[str], tuple[int, int, dict[str, object]] | None]
DefGetBaseName = Callable[[str], str]
DefIsSemanticTemplateVariant = Callable[[str, dict[str, object] | None], bool]
DefSniffRasterSize = Callable[[str | Path], tuple[int, int]]


def loadExistingConversionRowsImpl(
    output_root: str,
    folder_path: str,
    reports_output_dir_fn: Callable[[str], str],
    converted_svg_output_dir_fn: Callable[[str], str],
    read_svg_geometry_fn: DefReadSvgGeometry,
    get_base_name_fn: DefGetBaseName,
    is_semantic_template_variant_fn: DefIsSemanticTemplateVariant,
    sniff_raster_size_fn: DefSniffRasterSize,
) -> list[dict[str, object]]:
    """Load previously converted variants so they can act as donor templates."""
    reports_path = Path(reports_output_dir_fn(output_root)) / "Iteration_Log.csv"
    svg_out_dir = Path(converted_svg_output_dir_fn(output_root))
    if not reports_path.exists() or not svg_out_dir.exists():
        return []

    rows: list[dict[str, object]] = []
    try:
        with reports_path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f, delimiter=";")
            for raw_row in reader:
                filename = str(raw_row.get("Dateiname", "")).strip()
                if not filename:
                    continue

                variant = os.path.splitext(filename)[0].upper()
                svg_path = svg_out_dir / f"{variant}.svg"
                if not svg_path.exists():
                    continue

                geometry = read_svg_geometry_fn(str(svg_path))
                if geometry is None:
                    continue
                w, h, params = geometry
                base = get_base_name_fn(variant).upper()
                if is_semantic_template_variant_fn(base, params):
                    params["mode"] = "semantic_badge"

                error_per_pixel_raw = str(raw_row.get("FehlerProPixel", "")).strip().replace(",", ".")
                diff_score_raw = str(raw_row.get("Diff-Score", "")).strip().replace(",", ".")
                best_iter_raw = str(raw_row.get("Beste Iteration", "")).strip()
                image_path = Path(folder_path) / filename
                if image_path.exists():
                    try:
                        width, height = sniff_raster_size_fn(image_path)
                        w = int(width)
                        h = int(height)
                    except Exception:
                        pass

                try:
                    error_per_pixel = float(error_per_pixel_raw)
                except ValueError:
                    error_per_pixel = float("inf")
                try:
                    best_error = float(diff_score_raw)
                except ValueError:
                    best_error = float("inf")
                try:
                    best_iter = int(best_iter_raw)
                except ValueError:
                    best_iter = 0

                rows.append(
                    {
                        "filename": filename,
                        "params": params,
                        "best_iter": best_iter,
                        "best_error": best_error,
                        "error_per_pixel": error_per_pixel,
                        "w": int(w),
                        "h": int(h),
                        "base": base,
                        "variant": variant,
                    }
                )
    except OSError:
        return []

    return [
        row
        for row in rows
        if math.isfinite(float(row.get("error_per_pixel", float("inf"))))
    ]


def sniffRasterSizeImpl(path: str | Path) -> tuple[int, int]:
    file_path = Path(path)
    with file_path.open("rb") as fh:
        header = fh.read(32)

    if header.startswith(b"\x89PNG\r\n\x1a\n") and len(header) >= 24:
        return struct.unpack(">II", header[16:24])

    if header[:6] in {b"GIF87a", b"GIF89a"} and len(header) >= 10:
        return struct.unpack("<HH", header[6:10])

    if header.startswith(b"BM"):
        with file_path.open("rb") as fh:
            fh.seek(18)
            dib = fh.read(8)
        if len(dib) == 8:
            width, height = struct.unpack("<ii", dib)
            return abs(int(width)), abs(int(height))

    if header.startswith(b"\xff\xd8"):
        with file_path.open("rb") as fh:
            fh.seek(2)
            while True:
                marker_prefix = fh.read(1)
                if not marker_prefix:
                    break
                if marker_prefix != b"\xff":
                    continue
                marker = fh.read(1)
                while marker == b"\xff":
                    marker = fh.read(1)
                if marker in {b"\xd8", b"\xd9"}:
                    continue
                size_bytes = fh.read(2)
                if len(size_bytes) != 2:
                    break
                segment_size = struct.unpack(">H", size_bytes)[0]
                if marker in {
                    b"\xc0", b"\xc1", b"\xc2", b"\xc3",
                    b"\xc5", b"\xc6", b"\xc7",
                    b"\xc9", b"\xca", b"\xcb",
                    b"\xcd", b"\xce", b"\xcf",
                }:
                    payload = fh.read(5)
                    if len(payload) != 5:
                        break
                    height, width = struct.unpack(">HH", payload[1:5])
                    return int(width), int(height)
                fh.seek(max(0, segment_size - 2), os.SEEK_CUR)

    raise ValueError(f"Unsupported or unreadable raster image: {file_path}")
