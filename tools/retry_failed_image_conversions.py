from __future__ import annotations

import base64
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RetryResult:
    stem: str
    status: str
    output_path: Path | None = None
    reason: str | None = None


def _stem_from_failed_diff_name(filename: str) -> str | None:
    """Extract variant stem from failed diff image names.

    Supports both ``*_diff_failed.png`` and legacy ``*_failed.png`` names.
    """
    name = Path(filename).name
    for suffix in ("_diff_failed.png", "_failed.png"):
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return None


def _png_dimensions(png_bytes: bytes) -> tuple[int, int]:
    if len(png_bytes) < 24 or png_bytes[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("Unsupported or invalid PNG input")
    width = int.from_bytes(png_bytes[16:20], "big")
    height = int.from_bytes(png_bytes[20:24], "big")
    if width <= 0 or height <= 0:
        raise ValueError("Invalid PNG dimensions")
    return width, height


def _embedded_png_svg(png_bytes: bytes) -> str:
    width, height = _png_dimensions(png_bytes)
    encoded = base64.b64encode(png_bytes).decode("ascii")
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">'
        f'<image href="data:image/png;base64,{encoded}" width="{width}" height="{height}"/>'
        "</svg>"
    )


def retry_failed_conversions(
    *,
    diff_dir: Path,
    source_dir: Path,
    output_dir: Path,
    overwrite: bool = False,
) -> list[RetryResult]:
    """Retry failed image conversions by embedding original PNGs into SVG wrappers."""
    output_dir.mkdir(parents=True, exist_ok=True)

    results: list[RetryResult] = []
    for diff_path in sorted(diff_dir.glob("*_failed.png")):
        stem = _stem_from_failed_diff_name(diff_path.name)
        if stem is None:
            continue

        source_png = source_dir / f"{stem}.png"
        target_svg = output_dir / f"{stem}.svg"

        if not source_png.exists():
            results.append(RetryResult(stem=stem, status="missing_source", reason=str(source_png)))
            continue
        if target_svg.exists() and not overwrite:
            results.append(RetryResult(stem=stem, status="skipped_existing", output_path=target_svg))
            continue

        png_bytes = source_png.read_bytes()
        svg_content = _embedded_png_svg(png_bytes)
        target_svg.write_text(svg_content, encoding="utf-8")
        results.append(RetryResult(stem=stem, status="recovered", output_path=target_svg))

    return results
