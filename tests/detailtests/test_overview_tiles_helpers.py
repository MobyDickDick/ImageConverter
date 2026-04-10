from __future__ import annotations

import zlib
from pathlib import Path

from src import overviewTiles


def _build_png_bytes() -> bytes:
    raw = b"\x00\x00\x00\x00\x00"
    compressed = zlib.compress(raw)
    return (
        b"\x89PNG\r\n\x1a\n"
        + b"\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
        + len(compressed).to_bytes(4, "big")
        + b"IDAT"
        + compressed
        + zlib.crc32(b"IDAT" + compressed).to_bytes(4, "big")
        + b"\x00\x00\x00\x00IEND\xaeB`\x82"
    )


def test_has_valid_png_structure_accepts_valid_png(tmp_path: Path) -> None:
    png_path = tmp_path / "valid.png"
    png_path.write_bytes(_build_png_bytes())
    assert overviewTiles._hasValidPngStructure(png_path) is True


def test_has_valid_png_structure_rejects_bad_crc(tmp_path: Path) -> None:
    png_path = tmp_path / "broken.png"
    payload = bytearray(_build_png_bytes())
    payload[-6] ^= 0x01
    png_path.write_bytes(bytes(payload))
    assert overviewTiles._hasValidPngStructure(png_path) is False
