from pathlib import Path

from tools import plan_b_roundtrip


def test_write_varied_svg_wraps_sample_with_relative_transform(tmp_path: Path) -> None:
    sample = tmp_path / "sample.svg"
    sample.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="10" viewBox="0 0 20 10"><text x="10" y="5">P</text></svg>',
        encoding="utf-8",
    )
    target = tmp_path / "varied.svg"

    plan_b_roundtrip._write_varied_svg(sample, target, scale=2.0, rel_x=0.5, rel_y=-0.25)

    varied = target.read_text(encoding="utf-8")
    assert 'data-plan-b-variation="parameter-probe"' in varied
    assert 'translate(10.000000 -2.500000)' in varied
    assert 'scale(2.000000)' in varied
    assert '<text x="10" y="5">P</text>' in varied


def test_relative_variation_for_variant_is_deterministic_and_semantic() -> None:
    first = plan_b_roundtrip._relative_variation_for_variant("AC0732_1_M")
    second = plan_b_roundtrip._relative_variation_for_variant("AC0732_1_M")

    assert first == second
    assert 0.5 <= first[0] <= 2.0
    assert isinstance(first[3], str) and first[3]
