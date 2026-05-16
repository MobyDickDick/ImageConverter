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
from src.iCCModules.imageCompositeConverterDependencies import vendored_site_packages_dirs


def _create_svg_from_description(svg_path: Path, description: str) -> None:
    # Lightweight deterministic SVG template seeded by a free-text description.
    # The description is embedded as metadata and visible text to preserve traceability.
    safe_text = description.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512">
  <metadata>{safe_text}</metadata>
  <rect x="0" y="0" width="512" height="512" fill="#f8f9fb"/>
  <circle cx="256" cy="210" r="120" fill="#6aa9ff" stroke="#1e3a8a" stroke-width="8"/>
  <rect x="108" y="320" width="296" height="56" rx="20" fill="#0f172a"/>
  <line x1="128" y1="348" x2="384" y2="348" stroke="#38bdf8" stroke-width="8"/>
  <text x="256" y="214" font-size="38" text-anchor="middle" font-family="Arial" fill="#ffffff">Plan B</text>
  <text x="256" y="476" font-size="18" text-anchor="middle" font-family="Arial" fill="#334155">{safe_text}</text>
</svg>'''
    svg_path.write_text(svg, encoding="utf-8")


def _render_svg_to_jpeg(svg_path: Path, jpeg_path: Path) -> None:
    fitz = import_with_vendored_fallback("fitz")
    with fitz.open(svg_path) as doc:
        pix = doc[0].get_pixmap(alpha=False)
        pix.save(jpeg_path, output="jpeg", jpg_quality=95)


def _add_noise(jpeg_in: Path, jpeg_out: Path, sigma: float) -> None:
    fitz = import_with_vendored_fallback("fitz")
    import random

    with fitz.open(jpeg_in) as doc:
        pix = doc[0].get_pixmap(alpha=False)

    noisy = bytearray(pix.samples)
    channels = pix.n
    for i in range(0, len(noisy), channels):
        for ch in range(3):
            value = noisy[i + ch] + int(random.gauss(0.0, sigma))
            noisy[i + ch] = 0 if value < 0 else (255 if value > 255 else value)

    out_pix = fitz.Pixmap(fitz.csRGB, pix.width, pix.height, bytes(noisy), 0)
    out_pix.save(jpeg_out, output="jpeg", jpg_quality=92)


def main() -> int:
    p = argparse.ArgumentParser(description="Create synthetic Plan-B sample (description->SVG->JPEG->noise->convert).")
    p.add_argument("description", help="Natural-language scene description for the synthetic SVG.")
    p.add_argument("--variant", default="AC0080_L", help="Existing variant key expected by converter descriptions XML.")
    p.add_argument("--descriptions-path", type=Path, default=Path("artifacts/images_to_convert/Finale_Wurzelformen_V3.xml"))
    p.add_argument("--output-dir", type=Path, default=Path("artifacts/converted_images"))
    args = p.parse_args()

    with tempfile.TemporaryDirectory(prefix="plan_b_synth_") as tmp:
        tmp_dir = Path(tmp)
        svg_path = tmp_dir / f"{args.variant}_synthetic.svg"
        jpeg_clean = tmp_dir / f"{args.variant}.jpg"
        jpeg_noisy = tmp_dir / f"{args.variant}_noisy.jpg"

        _create_svg_from_description(svg_path, args.description)
        _render_svg_to_jpeg(svg_path, jpeg_clean)
        _add_noise(jpeg_clean, jpeg_noisy, sigma=7.5)

        converter_input = tmp_dir / "input"
        converter_input.mkdir(parents=True, exist_ok=True)
        (converter_input / f"{args.variant}.jpg").write_bytes(jpeg_noisy.read_bytes())

        import os

        env = dict(os.environ)
        vendored_paths = [str(p) for p in vendored_site_packages_dirs()]
        existing_pythonpath = env.get("PYTHONPATH", "")
        pythonpath_parts = [str(REPO_ROOT), *vendored_paths]
        if existing_pythonpath:
            pythonpath_parts.append(existing_pythonpath)
        env["PYTHONPATH"] = ":".join(part for part in pythonpath_parts if part)

        cmd = [
            sys.executable,
            "-m",
            "src.imageCompositeConverter",
            str(converter_input),
            "--descriptions-path",
            str(args.descriptions_path),
            "--output-dir",
            str(args.output_dir),
            "--start",
            args.variant,
            "--end",
            args.variant,
        ]
        subprocess.run(cmd, check=True, env=env)

    print(f"status=ok\nvariant={args.variant}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
