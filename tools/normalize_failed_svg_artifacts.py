#!/usr/bin/env python3
"""Normalize failed SVG artifact naming in converted_svgs directories.

Any plain `<variant>.svg` that contains a trivial 1x1 white placeholder canvas
or embedded raster payload is renamed to `Failed_<variant>.svg`.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


def svg_contains_embedded_raster(svg_path: Path) -> bool:
    try:
        content = svg_path.read_text(encoding="utf-8").lower()
    except OSError:
        return False

    if "data:image/" in content:
        return True
    if "<image" not in content:
        return False

    href_values = re.findall(r"(?:href|xlink:href)\s*=\s*['\"]([^'\"]+)['\"]", content)
    for href in href_values:
        if href.startswith("data:image/"):
            return True
        if re.search(r"\.(png|jpe?g|gif|webp|bmp|tiff?)(?:$|[?#])", href):
            return True
        if href.startswith("data:") and "base64," in href and "ivborw0kggo" in href:
            return True
    return False


def svg_is_trivial_fallback(svg_path: Path) -> bool:
    try:
        content = svg_path.read_text(encoding="utf-8").lower()
    except OSError:
        return False

    compact = re.sub(r"\s+", "", content)
    has_minimal_canvas = 'width="1"' in compact and 'height="1"' in compact and 'viewbox="0011"' in compact
    rect_match = re.search(r"<rect([^>]*)>", compact)
    rect_attrs = rect_match.group(1) if rect_match else ""
    has_white_rect = bool(rect_match) and bool(re.search(r"width=(['\"])100%\1", rect_attrs)) and bool(
        re.search(r"height=(['\"])100%\1", rect_attrs)
    ) and bool(re.search(r"fill=(['\"])#ffffff\1", rect_attrs))
    return has_minimal_canvas and has_white_rect


def normalize_directory(svg_dir: Path, *, dry_run: bool) -> list[tuple[Path, Path]]:
    if not svg_dir.exists():
        return []

    renames: list[tuple[Path, Path]] = []
    # First canonicalize legacy failed naming variants.
    for candidate in sorted(svg_dir.glob("*_failed.svg")):
        variant = candidate.stem[: -len("_failed")]
        if not variant:
            continue
        if variant.startswith("Failed_"):
            target = svg_dir / f"{variant}.svg"
        else:
            target = svg_dir / f"Failed_{variant}.svg"
        if candidate == target:
            continue
        renames.append((candidate, target))
        if dry_run:
            continue
        if target.exists():
            target.unlink()
        candidate.rename(target)

    for candidate in sorted(svg_dir.glob("failed_*.svg")):
        variant = candidate.stem[len("failed_") :]
        if not variant:
            continue
        if variant.startswith("Failed_"):
            target = svg_dir / f"{variant}.svg"
        else:
            target = svg_dir / f"Failed_{variant}.svg"
        if candidate == target:
            continue
        renames.append((candidate, target))
        if dry_run:
            continue
        if target.exists():
            target.unlink()
        candidate.rename(target)

    for candidate in sorted(svg_dir.glob("Failed_*_failed.svg")):
        variant = candidate.stem[len("Failed_") : -len("_failed")]
        if not variant:
            continue
        target = svg_dir / f"Failed_{variant}.svg"
        if candidate == target:
            continue
        renames.append((candidate, target))
        if dry_run:
            continue
        if target.exists():
            target.unlink()
        candidate.rename(target)

    # Then detect plain outputs that should be marked as failed.
    for svg_path in sorted(svg_dir.glob("*.svg")):
        if svg_path.name.startswith("Failed_"):
            continue
        if not (svg_is_trivial_fallback(svg_path) or svg_contains_embedded_raster(svg_path)):
            continue

        target = svg_path.with_name(f"Failed_{svg_path.name}")
        renames.append((svg_path, target))
        if dry_run:
            continue

        if target.exists():
            target.unlink()
        svg_path.rename(target)

    return renames


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "dirs",
        nargs="*",
        default=[
            "artifacts/converted_images/converted_svgs",
            "src/artifacts/converted_images/converted_svgs",
        ],
        help="Directories containing SVG conversion artifacts.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print planned renames without modifying files.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    total = 0
    for raw_dir in args.dirs:
        svg_dir = Path(raw_dir)
        renames = normalize_directory(svg_dir, dry_run=args.dry_run)
        for src, dst in renames:
            print(f"{src} -> {dst}")
        total += len(renames)
    print(f"renamed={total}{' (dry-run)' if args.dry_run else ''}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
