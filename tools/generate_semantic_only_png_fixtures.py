#!/usr/bin/env python3
"""Generate the tiny grayscale PNG inputs used by the semantic-only benchmark."""
from __future__ import annotations

import argparse
import struct
import zlib
from pathlib import Path


WIDTH = HEIGHT = 64


def _canvas() -> bytearray:
    return bytearray([245] * (WIDTH * HEIGHT))


def _point(pixels: bytearray, x: int, y: int, value: int) -> None:
    if 0 <= x < WIDTH and 0 <= y < HEIGHT:
        pixels[y * WIDTH + x] = value


def _line(
    pixels: bytearray,
    x0: int,
    y0: int,
    x1: int,
    y1: int,
    *,
    value: int = 55,
    width: int = 2,
) -> None:
    dx, step_x = abs(x1 - x0), 1 if x0 < x1 else -1
    dy, step_y = -abs(y1 - y0), 1 if y0 < y1 else -1
    error = dx + dy
    while True:
        for y in range(y0 - width // 2, y0 + width // 2 + 1):
            for x in range(x0 - width // 2, x0 + width // 2 + 1):
                _point(pixels, x, y, value)
        if (x0, y0) == (x1, y1):
            return
        doubled = 2 * error
        if doubled >= dy:
            error += dy
            x0 += step_x
        if doubled <= dx:
            error += dx
            y0 += step_y


def _png_bytes(pixels: bytearray) -> bytes:
    rows = b"".join(
        b"\0" + bytes(pixels[y * WIDTH : (y + 1) * WIDTH]) for y in range(HEIGHT)
    )

    def chunk(kind: bytes, payload: bytes) -> bytes:
        checksum = zlib.crc32(kind + payload) & 0xFFFFFFFF
        return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", checksum)

    header = struct.pack(">IIBBBBB", WIDTH, HEIGHT, 8, 0, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(
        b"IDAT", zlib.compress(rows)
    ) + chunk(b"IEND", b"")


def generate_fixtures(output_dir: Path) -> list[Path]:
    """Write all benchmark fixtures deterministically and return their paths."""
    output_dir.mkdir(parents=True, exist_ok=True)

    circle = _canvas()
    for y in range(HEIGHT):
        for x in range(WIDTH):
            distance_squared = (x - 25) ** 2 + (y - 32) ** 2
            if 17**2 <= distance_squared <= 20**2:
                _point(circle, x, y, 55)
    _line(circle, 45, 32, 62, 32, width=3)
    _line(circle, 20, 25, 20, 39, value=40, width=3)
    _line(circle, 20, 25, 29, 25, value=40, width=3)
    _line(circle, 20, 31, 27, 31, value=40, width=3)

    rectangle = _canvas()
    _line(rectangle, 10, 14, 53, 14, value=60)
    _line(rectangle, 53, 14, 53, 50, value=60)
    _line(rectangle, 53, 50, 10, 50, value=60)
    _line(rectangle, 10, 50, 10, 14, value=60)
    _line(rectangle, 14, 46, 49, 18, value=60, width=3)

    polygon = _canvas()
    _line(polygon, 12, 45, 31, 14, width=3)
    _line(polygon, 31, 14, 51, 45, width=3)
    _line(polygon, 51, 45, 12, 45, width=3)
    _line(polygon, 31, 14, 31, 55)

    fixtures = {
        "circle_text_connector.png": circle,
        "rectangle_diagonal.png": rectangle,
        "polygon_line.png": polygon,
    }
    paths: list[Path] = []
    for filename, pixels in fixtures.items():
        path = output_dir / filename
        path.write_bytes(_png_bytes(pixels))
        paths.append(path)
    return paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/semantic_only_png_benchmark/fixtures"),
    )
    args = parser.parse_args(argv)
    for path in generate_fixtures(args.output_dir):
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
