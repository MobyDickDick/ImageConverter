"""Quality pass config and SVG fallback helper functions."""

from __future__ import annotations

import base64
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
    raw = Path(input_path).read_bytes()
    encoded = base64.b64encode(raw).decode("ascii")
    mime_type = svgHrefMimeTypeImpl(input_path)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{safe_w}" height="{safe_h}" '
        f'viewBox="0 0 {safe_w} {safe_h}">\n'
        f'  <image width="{safe_w}" height="{safe_h}" '
        f'href="data:{mime_type};base64,{encoded}" />\n'
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
    early_abort_config: dict[str, object] = {
        "enabled": True,
        "probe_iterations": 3,
        "threshold_multiplier": 8.0,
    }
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as existing_file:
                existing_payload = json.load(existing_file)
            existing_early_abort = existing_payload.get("early_abort", {}) if isinstance(existing_payload, dict) else {}
            if isinstance(existing_early_abort, dict):
                early_abort_config.update(existing_early_abort)
        except (json.JSONDecodeError, OSError):
            pass

    payload = {
        "allowed_error_per_pixel": float(max(0.0, normalized_error_pp)),
        "skip_variants": sorted(set(skipped_variants)),
        "early_abort": early_abort_config,
        "notes": (
            "Varianten in skip_variants werden in Folge-Pässen nicht erneut konvertiert. "
            "early_abort prueft einen kurzen Probelauf gegen die gespeicherte Erfolgsgrenze; "
            "threshold_multiplier ist bewusst konservativ, um aufholbare Starts nicht abzubrechen. "
            "Loeschen der Datei setzt den Ablauf zurueck, dann werden wieder alle Bitmaps bearbeitet."
        ),
        "source": source,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")
