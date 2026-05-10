from __future__ import annotations

import argparse
import subprocess
import tempfile
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.iCCModules.imageCompositeConverterDependencies import import_with_vendored_fallback


def _render_svg_to_jpeg(svg_path: Path, jpeg_path: Path) -> None:
    fitz = import_with_vendored_fallback("fitz")
    with fitz.open(svg_path) as doc:
        pix = doc[0].get_pixmap(alpha=False)
        pix.save(jpeg_path, output="jpeg", jpg_quality=95)


def _delta2(path_a: Path, path_b: Path) -> float:
    fitz = import_with_vendored_fallback("fitz")
    with fitz.open(path_a) as a_doc, fitz.open(path_b) as b_doc:
        a_pix = a_doc[0].get_pixmap(alpha=False)
        b_pix = b_doc[0].get_pixmap(alpha=False)

    if (a_pix.width, a_pix.height) != (b_pix.width, b_pix.height):
        raise ValueError("Image dimensions differ; cannot compare delta2.")

    width = a_pix.width
    height = a_pix.height
    a_bytes = a_pix.samples
    b_bytes = b_pix.samples
    a_stride = a_pix.stride
    b_stride = b_pix.stride
    a_n = a_pix.n
    b_n = b_pix.n

    channel_sums = [0.0, 0.0, 0.0]
    pixel_count = width * height
    for y in range(height):
        a_row = y * a_stride
        b_row = y * b_stride
        for x in range(width):
            a_off = a_row + x * a_n
            b_off = b_row + x * b_n
            for ch in range(3):
                channel_sums[ch] += abs(a_bytes[a_off + ch] - b_bytes[b_off + ch])

    means = [s / pixel_count for s in channel_sums]
    return float(sum(m * m for m in means))


def main() -> int:
    p = argparse.ArgumentParser(description="Plan-B roundtrip probe: SVG->JPEG->Converter->SVG")
    p.add_argument("sample_svg", type=Path, help="Reference sample SVG (e.g. AC0080_L.svg)")
    p.add_argument("--converter-input-dir", type=Path, default=Path("artifacts/images_to_convert"))
    p.add_argument("--descriptions-path", type=Path, default=Path("artifacts/images_to_convert/Finale_Wurzelformen_V3.xml"))
    p.add_argument("--output-dir", type=Path, default=Path("artifacts/converted_images"))
    args = p.parse_args()

    sample_svg = args.sample_svg
    variant = sample_svg.stem

    with tempfile.TemporaryDirectory(prefix="plan_b_") as tmp:
        tmp_dir = Path(tmp)
        tmp_jpeg = tmp_dir / f"{variant}.jpg"
        _render_svg_to_jpeg(sample_svg, tmp_jpeg)

        converter_input = tmp_dir / "input"
        converter_input.mkdir(parents=True, exist_ok=True)
        (converter_input / tmp_jpeg.name).write_bytes(tmp_jpeg.read_bytes())

        cmd = [
            "python",
            "-m",
            "src.imageCompositeConverter",
            str(converter_input),
            "--descriptions-path",
            str(args.descriptions_path),
            "--output-dir",
            str(args.output_dir),
            "--start",
            variant,
            "--end",
            variant,
        ]
        subprocess.run(cmd, check=True)

    out_svg = args.output_dir / "converted_svgs" / f"{variant}.svg"
    if not out_svg.exists():
        failed_svg = args.output_dir / "converted_svgs" / f"Failed_{variant}.svg"
        if failed_svg.exists():
            print(f"variant={variant}")
            print("status=failed_svg")
            print(f"failed_svg={failed_svg}")
            return 1
        raise FileNotFoundError(f"No output SVG found for {variant}: {out_svg}")

    # Render output SVG to JPEG for direct pixel comparison.
    out_jpeg = args.output_dir / "reports" / f"{variant}_plan_b_out.jpeg"
    out_jpeg.parent.mkdir(parents=True, exist_ok=True)
    _render_svg_to_jpeg(out_svg, out_jpeg)

    sample_jpeg = args.output_dir / "reports" / f"{variant}_plan_b_sample.jpeg"
    _render_svg_to_jpeg(sample_svg, sample_jpeg)

    print(f"variant={variant}")
    print(f"output_svg={out_svg}")
    print(f"delta2_output_vs_sample={_delta2(out_jpeg, sample_jpeg):.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
