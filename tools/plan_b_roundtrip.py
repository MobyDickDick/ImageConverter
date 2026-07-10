from __future__ import annotations

import argparse
import re
import subprocess
import tempfile
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.iCCModules.imageCompositeConverterDependencies import import_with_vendored_fallback


_NUM = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)"


def _svg_viewport(svg_text: str) -> tuple[float, float, float, float]:
    viewbox = re.search(
        r"viewBox=[\"\']\s*(%s)\s+(%s)\s+(%s)\s+(%s)\s*[\"\']" % (_NUM, _NUM, _NUM, _NUM),
        svg_text,
    )
    if viewbox:
        return tuple(float(viewbox.group(i)) for i in range(1, 5))  # type: ignore[return-value]

    width = re.search(r"width=[\"\']\s*(%s)(?:px)?\s*[\"\']" % _NUM, svg_text)
    height = re.search(r"height=[\"\']\s*(%s)(?:px)?\s*[\"\']" % _NUM, svg_text)
    if width and height:
        return (0.0, 0.0, float(width.group(1)), float(height.group(1)))

    return (0.0, 0.0, 512.0, 512.0)


def _relative_variation_for_variant(variant: str) -> tuple[float, float, float, str]:
    """Return deterministic semantic variation: scale, relative-x, relative-y, label."""
    variations = [
        (0.5, 0.0, 0.0, "half-size centered"),
        (2.0, 0.0, 0.0, "double-size centered"),
        (1.0, 0.35, 0.0, "main element shifted right"),
        (1.0, -0.35, 0.0, "main element shifted left"),
        (1.0, 0.0, -0.35, "main element shifted upward"),
        (1.0, 0.0, 0.35, "main element shifted downward"),
        (1.35, 0.65, 0.0, "main element partly outside to the right"),
    ]
    return variations[sum(variant.encode("utf-8")) % len(variations)]


def _write_varied_svg(sample_svg: Path, target_svg: Path, *, scale: float, rel_x: float, rel_y: float) -> None:
    svg_text = sample_svg.read_text(encoding="utf-8")
    min_x, min_y, width, height = _svg_viewport(svg_text)
    cx = min_x + width / 2.0
    cy = min_y + height / 2.0
    dx = rel_x * width
    dy = rel_y * height
    transform = (
        f"translate({dx:.6f} {dy:.6f}) "
        f"translate({cx:.6f} {cy:.6f}) "
        f"scale({scale:.6f}) "
        f"translate({-cx:.6f} {-cy:.6f})"
    )
    open_tag = re.search(r"<svg\b[^>]*>", svg_text, flags=re.IGNORECASE | re.DOTALL)
    close_tag = re.search(r"</svg\s*>", svg_text, flags=re.IGNORECASE)
    if not open_tag or not close_tag:
        raise ValueError(f"Not an SVG document: {sample_svg}")
    varied = (
        f"{svg_text[:open_tag.end()]}\n"
        f"  <g data-plan-b-variation=\"parameter-probe\" transform=\"{transform}\">"
        f"{svg_text[open_tag.end():close_tag.start()]}"
        f"  </g>\n{svg_text[close_tag.start():]}"
    )
    target_svg.write_text(varied, encoding="utf-8")


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
    p.add_argument(
        "--scale",
        type=float,
        default=None,
        help="Optional relative SVG scale probe (recommended range: 0.5..2.0).",
    )
    p.add_argument(
        "--rel-x",
        type=float,
        default=None,
        help="Optional relative x-position probe in viewport widths; positive means right.",
    )
    p.add_argument(
        "--rel-y",
        type=float,
        default=None,
        help="Optional relative y-position probe in viewport heights; positive means down.",
    )
    args = p.parse_args()

    sample_svg = args.sample_svg
    variant = sample_svg.stem
    default_scale, default_rel_x, default_rel_y, variation_label = _relative_variation_for_variant(variant)
    scale = default_scale if args.scale is None else args.scale
    rel_x = default_rel_x if args.rel_x is None else args.rel_x
    rel_y = default_rel_y if args.rel_y is None else args.rel_y

    with tempfile.TemporaryDirectory(prefix="plan_b_") as tmp:
        tmp_dir = Path(tmp)
        varied_svg = tmp_dir / f"{variant}_plan_b_varied.svg"
        tmp_jpeg = tmp_dir / f"{variant}.jpg"
        _write_varied_svg(sample_svg, varied_svg, scale=scale, rel_x=rel_x, rel_y=rel_y)
        varied_svg_report = args.output_dir / "reports" / f"{variant}_plan_b_varied.svg"
        varied_svg_report.parent.mkdir(parents=True, exist_ok=True)
        varied_svg_report.write_text(varied_svg.read_text(encoding="utf-8"), encoding="utf-8")
        _render_svg_to_jpeg(varied_svg, tmp_jpeg)

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
    _render_svg_to_jpeg(varied_svg_report if "varied_svg_report" in locals() else sample_svg, sample_jpeg)

    print(f"variant={variant}")
    effective_label = (
        variation_label
        if args.scale is None and args.rel_x is None and args.rel_y is None
        else "custom relative SVG parameter probe"
    )
    print(f"plan_b_variation={effective_label}")
    print(f"variation_scale={scale:.6f}")
    print(f"variation_rel_x={rel_x:.6f}")
    print(f"variation_rel_y={rel_y:.6f}")
    print(f"varied_input_svg={varied_svg_report if 'varied_svg_report' in locals() else sample_svg}")
    print(f"output_svg={out_svg}")
    print(f"delta2_output_vs_sample={_delta2(out_jpeg, sample_jpeg):.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
