from __future__ import annotations

from src.iCCModules import imageCompositeConverterFormsSymmetricChords as symmetric_chords_helpers


def test_derive_symmetric_chord_spec_impl_extracts_angle_and_offset() -> None:
    spec = symmetric_chords_helpers.deriveSymmetricChordSpecImpl(
        cx=25.0,
        cy=25.0,
        r=24.0,
        top_line=symmetric_chords_helpers.LineSegment(
            x1=1.5454797,
            y1=20.540298,
            x2=39.167659,
            y2=5.9965364,
        ),
        circle_stroke_width=1.0,
    )

    assert round(spec.chord_angle_deg, 3) == 21.135
    assert round(spec.chord_offset, 3) == 13.527


def test_render_symmetric_chord_circle_svg_impl_adds_inner_clip_and_round_caps() -> None:
    spec = symmetric_chords_helpers.SymmetricChordCircleSpec(
        cx=25.0,
        cy=25.0,
        r=24.0,
        circle_fill="#d9d9d9",
        circle_stroke="#808080",
        circle_stroke_width=1.0,
        chord_stroke="#808080",
        chord_stroke_width=1.0,
        chord_angle_deg=21.136,
        chord_offset=4.462,
    )

    svg = symmetric_chords_helpers.renderSymmetricChordCircleSvgImpl(50, 50, spec)

    assert 'clipPath id="clipCircleInner"' in svg
    assert 'stroke-linecap="round"' in svg
    assert 'stroke-linejoin="round"' in svg
    assert svg.count("<line ") == 2
    assert svg.endswith("</svg>")


def test_render_symmetric_chord_circle_svg_impl_can_disable_inner_clipping() -> None:
    spec = symmetric_chords_helpers.SymmetricChordCircleSpec(cx=25.0, cy=25.0, r=24.0)

    svg = symmetric_chords_helpers.renderSymmetricChordCircleSvgImpl(
        50,
        50,
        spec,
        clip_to_inner_circle=False,
    )

    assert "clipPath" not in svg
