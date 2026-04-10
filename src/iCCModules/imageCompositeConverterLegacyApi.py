"""Legacy public API helpers for imageCompositeConverter."""

from __future__ import annotations

import json
import re
from pathlib import Path


def _normalizeFailedSvgTarget(target: Path) -> Path:
    """Return SVG output path with canonical ``Failed_`` prefix for fallback renders."""
    if target.suffix.lower() != ".svg":
        return target
    if re.match(r"(?i)^failed_", target.name):
        normalized_name = re.sub(r"(?i)^failed_", "Failed_", target.name, count=1)
        return target.with_name(normalized_name)
    return target.with_name(f"Failed_{target.name}")


def convertImageImpl(
    input_path: str,
    output_path: str,
    *,
    render_embedded_raster_svg_fn,
    detect_relevant_regions_fn,
    annotate_image_regions_fn,
    cv2_module,
    np_module,
) -> Path:
    """Backward-compatible single-image entrypoint implementation."""
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)

    if target.suffix.lower() == ".svg" or cv2_module is None or np_module is None:
        target = _normalizeFailedSvgTarget(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(render_embedded_raster_svg_fn(input_path), encoding="utf-8")
        return target

    img = cv2_module.imread(str(input_path))
    if img is None:
        raise FileNotFoundError(f"Bild konnte nicht gelesen werden: {input_path}")
    regions = detect_relevant_regions_fn(img)
    annotated = annotate_image_regions_fn(img, regions)
    cv2_module.imwrite(str(target), annotated)
    target.with_suffix(".json").write_text(json.dumps(regions, ensure_ascii=False, indent=2), encoding="utf-8")
    return target


def convertImageVariantsImpl(*args, convert_range_fn, **kwargs):
    """Compatibility shim implementation kept for tooling imports."""
    return convert_range_fn(*args, **kwargs)
