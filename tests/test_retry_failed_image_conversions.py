from __future__ import annotations

from pathlib import Path

from tools.retry_failed_image_conversions import _stem_from_failed_diff_name, retry_failed_conversions


def test_stem_from_failed_diff_name_supports_diff_suffix() -> None:
    assert _stem_from_failed_diff_name("AC0812_diff_failed.png") == "AC0812"
    assert _stem_from_failed_diff_name("AC0812_failed.png") == "AC0812"
    assert _stem_from_failed_diff_name("AC0812_diff.png") is None


def test_retry_failed_conversions_creates_embedded_svg(tmp_path: Path) -> None:
    diff_dir = tmp_path / "diff"
    source_dir = tmp_path / "images"
    output_dir = tmp_path / "svg"
    diff_dir.mkdir()
    source_dir.mkdir()

    (diff_dir / "AC0001_diff_failed.png").write_bytes(b"dummy")

    png_bytes = (
        b"\x89PNG\r\n\x1a\n"
        b"\x00\x00\x00\rIHDR"
        b"\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00"
        b"\x90wS\xde"
        b"\x00\x00\x00\x0cIDATx\x9cc```\x00\x00\x00\x04\x00\x01"
        b"\x0b\xe7\x02\x9b"
        b"\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    (source_dir / "AC0001.png").write_bytes(png_bytes)

    results = retry_failed_conversions(diff_dir=diff_dir, source_dir=source_dir, output_dir=output_dir, overwrite=False)

    assert len(results) == 1
    assert results[0].status == "recovered"

    svg_path = output_dir / "AC0001.svg"
    assert svg_path.exists()
    content = svg_path.read_text(encoding="utf-8")
    assert '<image href="data:image/png;base64,' in content
