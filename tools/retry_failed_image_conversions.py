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

    Supports ``*_failed_diff.png`` (current), ``*_diff_failed.png`` (legacy), and ``*_failed.png`` names.
    """
    name = Path(filename).name
    for suffix in ("_failed_diff.png", "_diff_failed.png", "_failed.png"):
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return None


def _resolve_source_raster(source_dir: Path, stem: str) -> Path | None:
    """Return the preferred source raster path for a failed conversion stem."""
    for suffix in (".png", ".jpg", ".jpeg", ".JPG", ".JPEG", ".PNG"):
        candidate = source_dir / f"{stem}{suffix}"
        if candidate.exists():
            return candidate
    return None


def _png_dimensions(png_bytes: bytes) -> tuple[int, int]:
    if len(png_bytes) < 24 or png_bytes[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("Unsupported or invalid PNG input")
    width = int.from_bytes(png_bytes[16:20], "big")
    height = int.from_bytes(png_bytes[20:24], "big")
    if width <= 0 or height <= 0:
        raise ValueError("Invalid PNG dimensions")
    return width, height


def _jpeg_dimensions(jpeg_bytes: bytes) -> tuple[int, int]:
    if len(jpeg_bytes) < 4 or jpeg_bytes[:2] != b"\xFF\xD8":
        raise ValueError("Unsupported or invalid JPEG input")

    i = 2
    while i + 1 < len(jpeg_bytes):
        if jpeg_bytes[i] != 0xFF:
            i += 1
            continue

        marker = jpeg_bytes[i + 1]
        i += 2

        # standalone markers without segment length
        if marker in {0xD8, 0xD9, 0x01} or 0xD0 <= marker <= 0xD7:
            continue

        if i + 1 >= len(jpeg_bytes):
            break

        seg_len = int.from_bytes(jpeg_bytes[i : i + 2], "big")
        if seg_len < 2 or i + seg_len > len(jpeg_bytes):
            break

        # SOF markers carrying width/height (exclude DHT/DAC/JPG)
        if marker in {
            0xC0,
            0xC1,
            0xC2,
            0xC3,
            0xC5,
            0xC6,
            0xC7,
            0xC9,
            0xCA,
            0xCB,
            0xCD,
            0xCE,
            0xCF,
        }:
            if seg_len < 7:
                break
            height = int.from_bytes(jpeg_bytes[i + 3 : i + 5], "big")
            width = int.from_bytes(jpeg_bytes[i + 5 : i + 7], "big")
            if width <= 0 or height <= 0:
                raise ValueError("Invalid JPEG dimensions")
            return width, height

        i += seg_len

    raise ValueError("Could not parse JPEG dimensions")


def _raster_dimensions_and_mime(source_raster: Path, raster_bytes: bytes) -> tuple[int, int, str]:
    suffix = source_raster.suffix.lower()
    if suffix == ".png":
        width, height = _png_dimensions(raster_bytes)
        return width, height, "image/png"

    if suffix in {".jpg", ".jpeg"}:
        width, height = _jpeg_dimensions(raster_bytes)
        return width, height, "image/jpeg"

    raise ValueError(f"Unsupported source format: {source_raster.suffix}")


def _embedded_raster_svg(raster_bytes: bytes, width: int, height: int, mime_type: str) -> str:
    encoded = base64.b64encode(raster_bytes).decode("ascii")
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">'
        f'<image href="data:{mime_type};base64,{encoded}" width="{width}" height="{height}"/>'
        "</svg>"
    )


def retry_failed_conversions(
    *,
    diff_dir: Path,
    source_dir: Path,
    output_dir: Path,
    overwrite: bool = False,
) -> list[RetryResult]:
    """Retry failed image conversions by embedding source rasters into SVG wrappers."""
    output_dir.mkdir(parents=True, exist_ok=True)

    results: list[RetryResult] = []
    failed_candidates = sorted({*diff_dir.glob("*_failed_diff.png"), *diff_dir.glob("*_diff_failed.png"), *diff_dir.glob("*_failed.png")})
    for diff_path in failed_candidates:
        stem = _stem_from_failed_diff_name(diff_path.name)
        if stem is None:
            continue

        source_raster = _resolve_source_raster(source_dir, stem)
        target_svg = output_dir / f"Failed_{stem}.svg"

        if source_raster is None:
            results.append(RetryResult(stem=stem, status="missing_source", reason=str(source_dir / f"{stem}.*")))
            continue
        if target_svg.exists() and not overwrite:
            results.append(RetryResult(stem=stem, status="skipped_existing", output_path=target_svg))
            continue

        raster_bytes = source_raster.read_bytes()
        width, height, mime_type = _raster_dimensions_and_mime(source_raster, raster_bytes)
        svg_content = _embedded_raster_svg(raster_bytes, width, height, mime_type)
        target_svg.write_text(svg_content, encoding="utf-8")
        results.append(RetryResult(stem=stem, status="recovered", output_path=target_svg))

    return results
