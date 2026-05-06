from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys

from src.iCCModules.imageCompositeConverterDependencies import import_with_vendored_fallback


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Validate SVG/JPEG sample pairs in a directory.")
    p.add_argument("samples_dir", type=Path, nargs="?", default=Path("artifacts/images_to_convert/samples"))
    p.add_argument(
        "--reference-dir",
        type=Path,
        default=Path("artifacts/images_to_convert"),
        help="Directory containing reference JPEG inputs for matching sample stems.",
    )
    p.add_argument("--strict", action="store_true", help="Return exit code 1 if any pair is missing.")
    p.add_argument(
        "--render-missing-jpeg",
        action="store_true",
        help="Render missing JPEG files from SVG samples before validating pairs.",
    )
    p.add_argument(
        "--report-csv",
        type=Path,
        default=None,
        help="Optional CSV report path for per-pair diff metrics.",
    )
    return p.parse_args()


def _render_svg_to_jpeg(svg_path: Path, jpeg_path: Path) -> None:
    fitz = import_with_vendored_fallback("fitz")

    with fitz.open(svg_path) as doc:
        page = doc[0]
        pix = page.get_pixmap(alpha=False)
        pix.save(jpeg_path, output="jpeg", jpg_quality=95)


def _diff_score(svg_jpeg: Path, reference_jpeg: Path) -> float:
    image_module = import_with_vendored_fallback("PIL.Image")
    image_chops_module = import_with_vendored_fallback("PIL.ImageChops")
    image_stat_module = import_with_vendored_fallback("PIL.ImageStat")

    Image = image_module
    ImageChops = image_chops_module
    ImageStat = image_stat_module

    with Image.open(svg_jpeg) as converted, Image.open(reference_jpeg) as reference:
        converted_rgb = converted.convert("RGB")
        reference_rgb = reference.convert("RGB")
        if converted_rgb.size != reference_rgb.size:
            converted_rgb = converted_rgb.resize(reference_rgb.size)
        diff = ImageChops.difference(converted_rgb, reference_rgb)
        stat = ImageStat.Stat(diff)
        mean_delta2 = sum(channel_mean * channel_mean for channel_mean in stat.mean)
    return float(mean_delta2)


def main() -> int:
    args = parse_args()
    samples_dir = args.samples_dir
    if not samples_dir.exists():
        print(f"samples directory not found: {samples_dir}")
        return 2

    svgs = {p.stem for p in samples_dir.glob("*.svg")}
    jpegs = {p.stem for p in samples_dir.glob("*.jpeg")} | {p.stem for p in samples_dir.glob("*.jpg")}

    if args.render_missing_jpeg:
        for stem in sorted(svgs - jpegs):
            svg_path = samples_dir / f"{stem}.svg"
            jpeg_path = samples_dir / f"{stem}.jpeg"
            _render_svg_to_jpeg(svg_path, jpeg_path)
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

    pair_metrics: list[dict[str, str | float]] = []
    for stem in sorted(svgs & jpegs):
        reference = args.reference_dir / f"{stem}.jpg"
        if not reference.exists():
            reference = args.reference_dir / f"{stem}.jpeg"
        if not reference.exists():
            continue
        rendered = samples_dir / f"{stem}.jpeg"
        if not rendered.exists():
            rendered = samples_dir / f"{stem}.jpg"
        mean_delta2 = _diff_score(rendered, reference)
        pair_metrics.append({"variant": stem, "mean_delta2": mean_delta2})

    if args.report_csv is not None:
        args.report_csv.parent.mkdir(parents=True, exist_ok=True)
        with args.report_csv.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["variant", "mean_delta2"], delimiter=";")
            writer.writeheader()
            for row in pair_metrics:
                writer.writerow({"variant": row["variant"], "mean_delta2": f"{row['mean_delta2']:.6f}"})
        print(f"report_csv={args.report_csv}")

    if not missing_jpeg and not orphan_jpeg:
        print("pair_validation=ok")
        return 0

    print("pair_validation=issues")
    return 1 if args.strict else 0


if __name__ == "__main__":
    sys.exit(main())
