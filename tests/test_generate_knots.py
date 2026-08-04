from pathlib import Path

import pytest

from tools.generate_knots import generate_knots, reduced_knot_specs


def test_specs_have_at_most_one_unknot_and_distinct_invariants() -> None:
    specs = reduced_knot_specs(8)
    assert sum(spec.is_unknot for spec in specs) == 1
    assert len({(spec.p, spec.q) for spec in specs}) == len(specs)
    assert [spec.crossing_number for spec in specs] == [0, 3, 5, 7, 9, 11, 13, 15]


def test_non_trivial_only_contains_reduced_knots() -> None:
    specs = reduced_knot_specs(4, include_unknot=False)
    assert all(not spec.is_unknot for spec in specs)
    assert all(spec.crossing_number == spec.q for spec in specs)


def test_generator_writes_matching_svg_and_png_pairs(tmp_path: Path) -> None:
    outputs = generate_knots(tmp_path, 3, size=96)
    assert len(outputs) == 3
    assert {path.suffix for pair in outputs for path in pair} == {".svg", ".png"}
    assert all(svg.stem == png.stem for svg, png in outputs)
    assert all('data-reduced="true"' in svg.read_text(encoding="utf-8") for svg, _ in outputs)
    assert all(png.read_bytes().startswith(b"\x89PNG\r\n\x1a\n") for _, png in outputs)


@pytest.mark.parametrize("count", [-1, -10])
def test_negative_count_is_rejected(count: int) -> None:
    with pytest.raises(ValueError, match="count"):
        reduced_knot_specs(count)
