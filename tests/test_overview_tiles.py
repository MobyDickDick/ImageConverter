from __future__ import annotations

from pathlib import Path

from src.overview_tiles import create_tiled_overview_svg, generate_conversion_overviews


def _write_svg(path: Path, body: str, *, width: int = 20, height: int = 10) -> None:
    path.write_text(
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}">{body}</svg>'
        ),
        encoding="utf-8",
    )


def test_create_tiled_overview_svg_contains_all_labels(tmp_path: Path) -> None:
    src_dir = tmp_path / "svg"
    src_dir.mkdir()
    _write_svg(src_dir / "A_1.svg", '<rect x="1" y="1" width="8" height="8" fill="#000"/>')
    _write_svg(src_dir / "B_2.svg", '<circle cx="5" cy="5" r="4" fill="#888"/>')

    out = tmp_path / "overview.svg"
    result = create_tiled_overview_svg(sorted(src_dir.glob("*.svg")), out, columns=2)

    assert result == out
    text = out.read_text(encoding="utf-8")
    assert "A_1" in text
    assert "B_2" in text
    assert "<svg" in text


def test_generate_conversion_overviews_writes_svg_vector_tile(tmp_path: Path) -> None:
    diff_dir = tmp_path / "diff"
    svg_dir = tmp_path / "svgs"
    reports_dir = tmp_path / "reports"
    diff_dir.mkdir()
    svg_dir.mkdir()
    reports_dir.mkdir()

    _write_svg(svg_dir / "AC0001.svg", '<rect x="0" y="0" width="20" height="10" fill="#555"/>')

    generated = generate_conversion_overviews(diff_dir, svg_dir, reports_dir)

    assert "svg_vector" in generated
    assert generated["svg_vector"].endswith("overview_svg_tiles.svg")
    assert (reports_dir / "overview_svg_tiles.svg").exists()
