#!/usr/bin/env python3
"""Resolve AC08 segment inputs and validate per-segment iteration evidence."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

IMAGE_EXTENSIONS = {".bmp", ".jpg", ".jpeg", ".png", ".gif", ".tif", ".tiff", ".webp"}


def resolve_variant_input_dir(input_root: Path, variant: str) -> Path:
    """Return the deterministic source directory containing ``variant``."""
    normalized_variant = variant.upper()
    matches = sorted(
        (
            path
            for path in input_root.rglob("*")
            if path.is_file()
            and path.suffix.lower() in IMAGE_EXTENSIONS
            and path.stem.upper() == normalized_variant
        ),
        key=lambda path: (len(path.relative_to(input_root).parts), str(path.relative_to(input_root))),
    )
    return matches[0].parent if matches else input_root


def iteration_report_contains_variant(report_path: Path, variant: str) -> bool:
    """Return whether an iteration report contains the expected variant row."""
    if not report_path.is_file():
        return False
    with report_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle, delimiter=";")
        next(reader, None)
        return any(row and Path(row[0]).stem.upper() == variant.upper() for row in reader)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    resolve_parser = subparsers.add_parser("resolve-input-dir")
    resolve_parser.add_argument("input_root", type=Path)
    resolve_parser.add_argument("variant")

    check_parser = subparsers.add_parser("check-iteration-report")
    check_parser.add_argument("report_path", type=Path)
    check_parser.add_argument("variant")

    args = parser.parse_args()
    if args.command == "resolve-input-dir":
        print(resolve_variant_input_dir(args.input_root, args.variant))
        return 0
    return 0 if iteration_report_contains_variant(args.report_path, args.variant) else 1


if __name__ == "__main__":
    raise SystemExit(main())
