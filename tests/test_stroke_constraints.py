"""Displayed width contracts, shared fitting, and actual saved raster evidence."""
from xml.etree import ElementTree as ET

import numpy as np
from PIL import Image
import pytest

from src.iCCModules.imageCompositeConverterDescriptionLanguage import (
    DescriptionRejected, description_assertions, validate_svg_assertions,
)
from src.iCCModules.imageCompositeConverterStrokeConstraints import constrain_stroke_width
from src.imageConverterSample import refine, render_svg


CONDITION = 'Alle Linien sind gleich breit.'


def scene(body):
    return '<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">'+body+'</svg>'


def linework(a, b):
    return scene(f'<line x1="8" y1="15" x2="55" y2="15" stroke="black" stroke-width="{a}"/>'
                 f'<line x1="8" y1="40" x2="55" y2="40" stroke="black" stroke-width="{b}"/>')


@pytest.mark.parametrize('condition', [CONDITION, 'Alle Linien haben die gleiche Strichstärke.',
    'Einheitliche Linienstärke.', 'Sämtliche Konturen sind gleich dick.',
    'Alle Striche müssen gleich breit sein.', 'Keine Schriftzeichen und alle Linien sind gleich breit.'])
def test_positive_global_width_condition_is_understood(condition):
    assert description_assertions(condition)['equal_stroke_width']


@pytest.mark.parametrize('condition', ['Nicht alle Linien sind gleich breit.',
    'Alle Linien sind nicht gleich breit.', 'Keine einheitliche Linienstärke.',
    'Ohne eine einheitliche Linienstärke.', 'Nicht zwingend alle Linien sind gleich breit.',
    'Die Beschriftung lautet "Alle Linien sind gleich breit".',
    'Die Beschriftung lautet „Einheitliche Linienstärke“.', 'Ein Kreis mit zwei Linien.'])
def test_width_constraint_does_not_come_from_negation_quotes_or_absence(condition):
    assertions = description_assertions(condition)
    assert not assertions.get('equal_stroke_width')
    svg = linework(1, 3)
    assert constrain_stroke_width(svg, assertions) == svg


@pytest.mark.parametrize('exception', ['ausser der roten Linie', 'mit Ausnahme der Randkontur'])
def test_unresolved_width_exceptions_are_reported_instead_of_overridden(exception):
    with pytest.raises(DescriptionRejected, match='unsupported_line_width_exception'):
        description_assertions('Alle Linien sind gleich breit, '+exception+'.')


@pytest.mark.parametrize('body', [
    '<g stroke="black" stroke-width="2"><line x2="20"/><path d="M0 8 L20 8"/></g>',
    '<style>.s {stroke:black;stroke-width:2px}</style><line class="s" x2="20"/>'
    '<line x2="20" y1="8" y2="8" style="stroke:black;stroke-width:2"/>',
    '<line x2="20" stroke="black" stroke-width="2"/>'
    '<g transform="translate(2 2) rotate(20) scale(2)"><circle r="4" stroke="red" stroke-width="1"/></g>',
    '<defs><line x2="20" stroke="black" stroke-width="99"/></defs>'
    '<g display="none"><line x2="20" stroke="black" stroke-width="17"/></g>'
    '<line x2="20" stroke="black" stroke-width="2"/>'
    '<line x2="20" stroke="black" stroke-width="42" opacity="0"/>',
    '<rect x="9" y="5" width="2" height="40"/>'
    '<rect x="9" y="35" width="40" height="2"/>',
])
def test_equal_displayed_widths_include_styles_inheritance_transforms_and_rectangles(body):
    validate_svg_assertions(scene(body), description_assertions(CONDITION))


@pytest.mark.parametrize('body', [
    '<line x2="20" stroke="black" stroke-width="1"/><path d="M0 8 L20 8" stroke="black" stroke-width="2"/>',
    '<line x2="20" stroke="black" stroke-width="1"/>'
    '<g transform="scale(2)"><line x2="20" stroke="black" stroke-width="1"/></g>',
    '<rect width="2" height="40"/><rect y="30" width="40" height="1"/>',
    '<g stroke="black" stroke-width="1"><line x2="20"/><line x2="20" stroke-width="2"/></g>',
])
def test_unequal_native_widths_are_rejected_even_without_other_assertions(body):
    with pytest.raises(DescriptionRejected, match='unequal_line_widths'):
        validate_svg_assertions(scene(body), description_assertions(CONDITION))


def test_nonsquare_viewport_compares_displayed_horizontal_and_vertical_widths():
    svg = ('<svg width="128" height="64" viewBox="0 0 64 64" preserveAspectRatio="none">'
           '<g stroke="black"><line x2="20"/><line y2="20"/></g></svg>')
    with pytest.raises(DescriptionRejected, match='unequal_line_widths'):
        validate_svg_assertions(svg, description_assertions(CONDITION))
    validate_svg_assertions(constrain_stroke_width(svg, description_assertions(CONDITION)),
                            description_assertions(CONDITION))


def test_curved_strokes_with_nonuniform_transforms_are_not_falsely_certified():
    svg = scene('<g transform="scale(2 1)"><circle r="4" stroke="black"/></g>')
    with pytest.raises(DescriptionRejected, match='nonuniform_line_width_transform'):
        validate_svg_assertions(svg, description_assertions(CONDITION))


def test_shared_width_keeps_bar_centers_and_handles_nested_strokes():
    svg = scene('<rect x="9" y="4" width="2" height="40"/>'
                '<rect x="10" y="30" width="40" height="1"/>'
                '<g transform="scale(2)" stroke="black"><path d="M5 5 L15 5"/></g>')
    constrained = constrain_stroke_width(svg, description_assertions(CONDITION), width=3)
    validate_svg_assertions(constrained, description_assertions(CONDITION))
    nodes = list(ET.fromstring(constrained))
    assert float(nodes[0].get('x'))+float(nodes[0].get('width'))/2 == 10
    assert float(nodes[1].get('y'))+float(nodes[1].get('height'))/2 == 30.5
    assert float(nodes[2][0].get('stroke-width')) == 1.5


def test_widening_a_short_bar_cannot_silently_exclude_it_from_linework():
    svg = scene('<rect width="1" height="4" stroke="black" stroke-width="0"/>'
                '<line y1="15" y2="15" x2="40" stroke="black" stroke-width="8"/>')
    constrained = constrain_stroke_width(svg, description_assertions(CONDITION), width=8)
    nodes = list(ET.fromstring(constrained))
    assert float(nodes[0].get('width')) < 4/3
    assert float(nodes[0].get('width')) == float(nodes[1].get('stroke-width'))
    validate_svg_assertions(constrained, description_assertions(CONDITION))


def test_width_violation_cannot_become_a_pixel_perfect_checkpoint():
    from src.iCCModules.imageCompositeConverterAdaptiveSearch import ImageSearch, SearchPolicy, image_search
    from src.iCCModules.imageCompositeConverterSearchPortfolio import validated_result
    session = ImageSearch(SearchPolicy())
    session.description_assertions = description_assertions(CONDITION)
    svg = linework(1, 3)
    image = render_svg(svg, 64, 64)
    session.bind_reference(image)
    saved = []
    session.on_validated = lambda *args: saved.append(args)
    with image_search(session), pytest.raises(DescriptionRejected, match='unequal_line_widths'):
        validated_result(dict(svg=svg, rendered=image), image)
    assert not saved and not session.validated


def test_sample_search_fits_one_common_width_and_preserves_uploaded_file(tmp_path):
    source, sample, output = [tmp_path/name for name in ('source.png', 'sample.svg', 'result.svg')]
    target = render_svg(linework(3, 3), 64, 64)
    Image.fromarray(target).save(source)
    original = linework(1, 2)
    sample.write_text(original, encoding='utf-8')
    report = refine(source, sample, output, 'Zwei horizontale Linien. '+CONDITION, 2.)
    assert report['passed'], report
    assert report['final_mse'] < report['initial_mse']*.1
    assert sample.read_text(encoding='utf-8') == original
    actual = output.read_text(encoding='utf-8')
    validate_svg_assertions(actual, description_assertions(CONDITION))
    mse = np.square(target.astype(float)-render_svg(actual, 64, 64).astype(float)).mean()/255**2
    assert report['final_mse'] == pytest.approx(mse)


def test_recovery_renders_and_saves_the_constrained_candidate(tmp_path):
    from src.imageConverterRecovery import recover
    source, candidate, output = [tmp_path/name for name in ('source.png', 'candidate.svg', 'result.svg')]
    target = render_svg(linework(2, 2), 64, 64)
    Image.fromarray(target).save(source)
    candidate.write_text(linework(1, 3), encoding='utf-8')
    report = recover(source, output, 'Zwei horizontale Linien. '+CONDITION, .5, candidate=candidate)
    assert report['passed'], report
    validate_svg_assertions(output.read_text(encoding='utf-8'), description_assertions(CONDITION))
    np.testing.assert_array_equal(render_svg(output.read_text(encoding='utf-8'), 64, 64), target)


def test_vector_search_fits_one_width_instead_of_separate_lines(tmp_path):
    from src.imageConverterRecovery import recover
    source, candidate, output = [tmp_path/name for name in ('source.png', 'candidate.svg', 'result.svg')]
    target = render_svg(linework(3, 3), 64, 64)
    Image.fromarray(target).save(source)
    candidate.write_text(linework(1, 2), encoding='utf-8')
    report = recover(source, output, 'Zwei horizontale Linien. '+CONDITION, 1., candidate=candidate)
    assert report['passed'], report
    assert report['revision'] > 1
    actual = output.read_text(encoding='utf-8')
    validate_svg_assertions(actual, description_assertions(CONDITION))
    mse = np.square(target.astype(float)-render_svg(actual, 64, 64).astype(float)).mean()/255**2
    assert mse == pytest.approx(report['normalized_mse'])
    initial = render_svg(linework(1.5, 1.5), 64, 64)
    initial_mse = np.square(target.astype(float)-initial.astype(float)).mean()/255**2
    assert mse < initial_mse*.3


def test_gui_final_validation_rejects_unequal_widths(tmp_path):
    from src.imageConverterGui import result_description_error
    result = tmp_path/'result.svg'
    result.write_text(linework(1, 3), encoding='utf-8')
    assert result_description_error(result, CONDITION) == 'unequal_line_widths'
    result.write_text(linework(2, 2), encoding='utf-8')
    assert result_description_error(result, CONDITION) == ''


def test_reference_inheritance_keeps_global_width_constraint():
    from src.iCCModules.imageCompositeConverterPerceptionReflection import Reflection
    reflection = Reflection({'neutral': 'Wie ZZ1234. '+CONDITION})
    reflection._inherit_mode_from_reference = lambda **kw: ('reference', dict(
        mode='non_composite', elements=[], language_assertions=dict(counts=[], no_text=False)))
    _, params = reflection.parse_description('neutral', 'neutral.png')
    assert params['language_assertions']['equal_stroke_width']
