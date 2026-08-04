"""Generate a pairwise-distinct collection of reduced knot diagrams.

The non-trivial diagrams are the (2, q) torus knots for odd q >= 3.  Their
standard alternating projection is reduced and has the minimal crossing number
q; consequently Reidemeister I/II cannot simplify it further.  Using a
different q for every output also makes the knots pairwise non-isotopic.

Only the Python standard library is used.  This is intentional: the PNG is a
real raster companion of the same sampled curve and does not depend on a local
SVG renderer being installed.
"""

from __future__ import annotations

import argparse
import math
import struct
import zlib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class KnotSpec:
    """Canonical, already Reidemeister-reduced output specification."""

    name: str
    p: int
    q: int
    crossing_number: int

    @property
    def is_unknot(self) -> bool:
        return self.crossing_number == 0


def reduced_knot_specs(count: int, *, include_unknot: bool = True) -> list[KnotSpec]:
    """Return ``count`` distinct reduced knots, with at most one unknot."""

    if count < 0:
        raise ValueError("count must not be negative")
    specs: list[KnotSpec] = []
    if count and include_unknot:
        specs.append(KnotSpec("unknot", 1, 1, 0))
    q = 3
    while len(specs) < count:
        specs.append(KnotSpec(f"torus_2_{q}", 2, q, q))
        q += 2
    return specs


def _curve(spec: KnotSpec, size: int, samples: int) -> list[tuple[float, float, float]]:
    if spec.is_unknot:
        return [
            (size / 2 + size * .34 * math.cos(t), size / 2 + size * .34 * math.sin(t), 0.0)
            for t in (2 * math.pi * i / samples for i in range(samples + 1))
        ]

    points = []
    # A generic tilted projection of a torus embedding.  The tilt prevents the
    # degenerate multiple intersections of an untilted axial projection.
    for i in range(samples + 1):
        t = 2 * math.pi * i / samples
        radius = 2.0 + .72 * math.cos(spec.q * t)
        x = radius * math.cos(spec.p * t)
        y = radius * math.sin(spec.p * t)
        z = .72 * math.sin(spec.q * t)
        y, z = y * .82 - z * .57, y * .57 + z * .82
        x, z = x * .94 + z * .34, -x * .34 + z * .94
        scale = size * .145
        points.append((size / 2 + scale * x, size / 2 + scale * y, z))
    return points


def _segments(points: list[tuple[float, float, float]]):
    return sorted(zip(points, points[1:]), key=lambda pair: (pair[0][2] + pair[1][2]) / 2)


def svg_text(spec: KnotSpec, *, size: int = 512, samples: int | None = None) -> str:
    """Render a knot as SVG with depth-sorted, white-separated crossings."""

    samples = samples or max(720, spec.q * 160)
    segments = _segments(_curve(spec, size, samples))
    casings = []
    strokes = []
    for (x1, y1, _), (x2, y2, _) in segments:
        coordinates = f'x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}"'
        casings.append(f'  <line {coordinates} stroke="white" stroke-width="12" stroke-linecap="round"/>')
        strokes.append(f'  <line {coordinates} stroke="black" stroke-width="6" stroke-linecap="round"/>')
    title = "Unknot" if spec.is_unknot else f"T(2,{spec.q}), {spec.crossing_number} crossings"
    return "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}"',
        f'     data-knot="{spec.name}" data-crossings="{spec.crossing_number}" data-reduced="true">',
        f"  <title>{title}</title>",
        f'  <rect width="{size}" height="{size}" fill="white"/>',
        *casings,
        *strokes,
        "</svg>", "",
    ])


def _paint_line(pixels: bytearray, size: int, a: tuple[float, float, float], b: tuple[float, float, float], width: int, value: int) -> None:
    x1, y1, _ = a; x2, y2, _ = b
    steps = max(1, int(max(abs(x2 - x1), abs(y2 - y1)) * 2))
    radius = width // 2
    for step in range(steps + 1):
        x = round(x1 + (x2 - x1) * step / steps)
        y = round(y1 + (y2 - y1) * step / steps)
        for py in range(max(0, y - radius), min(size, y + radius + 1)):
            for px in range(max(0, x - radius), min(size, x + radius + 1)):
                if (px - x) ** 2 + (py - y) ** 2 <= radius ** 2:
                    offset = (py * size + px) * 3
                    pixels[offset:offset + 3] = bytes((value, value, value))


def png_bytes(spec: KnotSpec, *, size: int = 512, samples: int | None = None) -> bytes:
    """Rasterize the same depth-ordered diagram into an RGB PNG."""

    samples = samples or max(720, spec.q * 160)
    pixels = bytearray(b"\xff" * (size * size * 3))
    segments = _segments(_curve(spec, size, samples))
    for a, b in segments:
        _paint_line(pixels, size, a, b, 12, 255)
    for a, b in segments:
        _paint_line(pixels, size, a, b, 6, 0)
    raw = b"".join(b"\x00" + pixels[row * size * 3:(row + 1) * size * 3] for row in range(size))
    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")


def generate_knots(output_dir: Path, count: int, *, include_unknot: bool = True, size: int = 512) -> list[tuple[Path, Path]]:
    """Write exactly one SVG/PNG pair per distinct knot."""

    if size < 64:
        raise ValueError("size must be at least 64 pixels")
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = []
    for index, spec in enumerate(reduced_knot_specs(count, include_unknot=include_unknot)):
        stem = f"knot_{index:03d}_{spec.name}"
        svg_path, png_path = output_dir / f"{stem}.svg", output_dir / f"{stem}.png"
        svg_path.write_text(svg_text(spec, size=size), encoding="utf-8")
        png_path.write_bytes(png_bytes(spec, size=size))
        outputs.append((svg_path, png_path))
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate pairwise-distinct, Reidemeister-reduced knots as SVG and PNG")
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/generated_knots"))
    parser.add_argument("--count", type=int, default=10)
    parser.add_argument("--size", type=int, default=512)
    parser.add_argument("--no-unknot", action="store_true", help="generate only non-trivial knots")
    args = parser.parse_args()
    outputs = generate_knots(args.output_dir, args.count, include_unknot=not args.no_unknot, size=args.size)
    print(f"generated_knots={len(outputs)}")
    print(f"generated_files={len(outputs) * 2}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
