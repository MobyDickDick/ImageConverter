#!/usr/bin/env python3
"""Convert exactly one image variant and optionally freeze it as regression baseline."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from tools.manage_satisfactory_baseline import prepare_baseline_pairs
from tools.run_catalog_conversion import conversion_environment

SUPPORTED_SUFFIXES = (".jpg", ".jpeg", ".png", ".bmp")


def existing_image_path(input_dir: Path, variant: str) -> Path:
    """Return the unique image path for a variant stem."""

    matches = [input_dir / f"{variant}{suffix}" for suffix in SUPPORTED_SUFFIXES]
    existing = [path for path in matches if path.exists()]
    if len(existing) != 1:
        candidates = ", ".join(str(path) for path in matches)
        raise FileNotFoundError(f"Expected exactly one source image for {variant}; checked: {candidates}")
    return existing[0]


def converted_svg_path(output_dir: Path, variant: str) -> Path:
    return output_dir / "converted_svgs" / f"{variant}.svg"


def build_converter_command(
    *,
    input_dir: Path,
    descriptions_path: Path,
    output_dir: Path,
    variant: str,
    iterations: int,
) -> list[str]:
    return [
        sys.executable,
        "-m",
        "src.imageCompositeConverter",
        str(input_dir),
        "--descriptions-path",
        str(descriptions_path),
        "--output-dir",
        str(output_dir),
        "--iterations",
        str(iterations),
        "--start",
        variant,
        "--end",
        variant,
        "--deterministic-order",
        "--fail-on-batch-failures",
    ]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("variant", help="Exact image stem to convert, for example AC0800_L.")
    parser.add_argument("--input-dir", type=Path, default=Path("artifacts/images_to_convert"))
    parser.add_argument(
        "--descriptions-path",
        type=Path,
        default=Path("artifacts/images_to_convert/Finale_Wurzelformen_V3.xml"),
    )
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/one-image-conversions"))
    parser.add_argument("--iterations", type=int, default=64)
    parser.add_argument("--timeout-seconds", type=float, default=60.0)
    parser.add_argument(
        "--freeze-baseline",
        action="store_true",
        help="After a successful conversion, copy the image/SVG pair into the satisfactory regression baseline.",
    )
    parser.add_argument(
        "--baseline-dir",
        type=Path,
        default=Path("artifacts/regression_baseline/satisfactory"),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    image_path = existing_image_path(args.input_dir, args.variant)
    run_output_dir = args.output_dir / args.variant
    run_output_dir.mkdir(parents=True, exist_ok=True)
    command = build_converter_command(
        input_dir=args.input_dir,
        descriptions_path=args.descriptions_path,
        output_dir=run_output_dir,
        variant=args.variant,
        iterations=args.iterations,
    )
    env = conversion_environment()
    env["ICC_CONVERSION_TIMEOUT_SEC"] = str(args.timeout_seconds)
    result = subprocess.run(command, env=env, check=False, timeout=args.timeout_seconds + 15.0)
    if result.returncode != 0:
        return result.returncode

    svg_path = converted_svg_path(run_output_dir, args.variant)
    if not svg_path.exists():
        print(f"[ONE-IMAGE] ERROR: converter completed but did not write {svg_path}", file=sys.stderr)
        return 1

    if args.freeze_baseline:
        prepared, missing = prepare_baseline_pairs(
            [args.variant],
            images_dir=image_path.parent,
            svgs_dir=svg_path.parent,
            baseline_dir=args.baseline_dir,
            move=False,
            append_manifest=True,
        )
        if missing or prepared != [args.variant]:
            print(f"[ONE-IMAGE] ERROR: baseline freeze incomplete; missing={missing}", file=sys.stderr)
            return 1
        print(f"[ONE-IMAGE] baseline_frozen={args.baseline_dir} variant={args.variant}")

    print(f"[ONE-IMAGE] converted={args.variant} svg={svg_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
