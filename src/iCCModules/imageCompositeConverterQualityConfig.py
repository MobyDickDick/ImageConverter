"""Quality pass config and SVG fallback helper functions."""

from __future__ import annotations

import json
import math
import os
from pathlib import Path


def svgHrefMimeTypeImpl(path: str | Path) -> str:
    ext = Path(path).suffix.lower()
    return {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".bmp": "image/bmp",
    }.get(ext, "application/octet-stream")


def renderEmbeddedRasterSvgImpl(
    input_path: str | Path,
    *,
    sniff_raster_size_fn,
) -> str:
    width, height = sniff_raster_size_fn(input_path)
    safe_w = max(1, int(width))
    safe_h = max(1, int(height))
    label = Path(input_path).name
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{safe_w}" height="{safe_h}" '
        f'viewBox="0 0 {safe_w} {safe_h}">\n'
        f'  <rect x="0" y="0" width="{safe_w}" height="{safe_h}" fill="#f5f5f5" stroke="#999" stroke-width="1"/>\n'
        f'  <text x="{max(4, safe_w // 20)}" y="{max(14, safe_h // 2)}" fill="#444" font-size="12" font-family="Arial, sans-serif">'
        f'Fallback (no embedded raster): {label}</text>\n'
        '</svg>\n'
    )


def qualityConfigPathImpl(reports_out_dir: str) -> str:
    return os.path.join(reports_out_dir, "quality_tercile_config.json")


def loadQualityConfigImpl(reports_out_dir: str, *, quality_config_path_fn) -> dict[str, object]:
    path = quality_config_path_fn(reports_out_dir)
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}
    return payload if isinstance(payload, dict) else {}


def writeQualityConfigImpl(
    reports_out_dir: str,
    *,
    allowed_error_per_pixel: float,
    skipped_variants: list[str],
    source: str,
    quality_config_path_fn,
) -> None:
    path = quality_config_path_fn(reports_out_dir)
    normalized_error_pp = float(allowed_error_per_pixel) if math.isfinite(allowed_error_per_pixel) else 0.0
    payload = {
        "allowed_error_per_pixel": float(max(0.0, normalized_error_pp)),
        "skip_variants": sorted(set(skipped_variants)),
        "notes": (
            "Varianten in skip_variants werden in Folge-Pässen nicht erneut konvertiert. "
            "Loeschen der Datei setzt den Ablauf zurueck, dann werden wieder alle Bitmaps bearbeitet."
        ),
        "source": source,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")
