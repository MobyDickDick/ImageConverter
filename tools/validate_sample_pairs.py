from __future__ import annotations

import argparse
from pathlib import Path
import sys


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Validate SVG/JPEG sample pairs in a directory.")
    p.add_argument("samples_dir", type=Path, nargs="?", default=Path("artifacts/images_to_convert/samples"))
    p.add_argument("--strict", action="store_true", help="Return exit code 1 if any pair is missing.")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    samples_dir = args.samples_dir
    if not samples_dir.exists():
        print(f"samples directory not found: {samples_dir}")
        return 2

    svgs = {p.stem for p in samples_dir.glob("*.svg")}
    jpegs = {p.stem for p in samples_dir.glob("*.jpeg")} | {p.stem for p in samples_dir.glob("*.jpg")}

    missing_jpeg = sorted(svgs - jpegs)
    orphan_jpeg = sorted(jpegs - svgs)

    print(f"svg_count={len(svgs)} jpeg_count={len(jpegs)}")
    if missing_jpeg:
        print("missing_jpeg_for_svg:")
        for stem in missing_jpeg:
            print(f"  - {stem}")
    if orphan_jpeg:
        print("orphan_jpeg_without_svg:")
        for stem in orphan_jpeg:
            print(f"  - {stem}")

    if not missing_jpeg and not orphan_jpeg:
        print("pair_validation=ok")
        return 0

    print("pair_validation=issues")
    return 1 if args.strict else 0


if __name__ == "__main__":
    sys.exit(main())
