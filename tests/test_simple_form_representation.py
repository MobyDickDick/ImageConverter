"""Every supported native form should prefer one analytic object over fragments."""
from xml.etree import ElementTree as ET

import numpy as np
import pytest

from src.iCCModules.imageCompositeConverterDescriptionLanguage import description_assertions, draft_assertions, validate_svg_assertions
from src.iCCModules.imageCompositeConverterRepresentation import representation_cost, simplification_proposals
from src.iCCModules.imageCompositeConverterAdaptiveSearch import ImageSearch, SearchPolicy, image_search
from src.iCCModules.imageCompositeConverterFallbackStructure import explore_structures
from src.imageConverterSample import render_svg


def scene(body):
    return '<svg xmlns="http://www.w3.org/2000/svg" width="80" height="80" viewBox="0 0 80 80"><rect width="80" height="80" fill="white"/>'+body+'</svg>'


def polygon(points):
    return '<polygon points="'+' '.join(f'{x:.6f},{y:.6f}' for x, y in points)+'" fill="#668899"/>'


def densify(points):
    return np.array([a*(1-t)+b*t for a, b in zip(points, np.roll(points, -1, axis=0)) for t in np.arange(0, 1, .1)])


@pytest.mark.parametrize('kind,body', [
    ('rect', polygon(densify(np.array([[15, 15], [65, 15], [65, 65], [15, 65]])))),
    ('polygon', polygon(densify(np.array([[40, 12], [65, 65], [15, 65]])))),
    ('circle', polygon(np.c_[40+25*np.cos(np.linspace(0, 2*np.pi, 80, endpoint=False)), 40+25*np.sin(np.linspace(0, 2*np.pi, 80, endpoint=False))])),
    ('ellipse', polygon(np.c_[40+28*np.cos(np.linspace(0, 2*np.pi, 100, endpoint=False)), 40+18*np.sin(np.linspace(0, 2*np.pi, 100, endpoint=False))])),
    ('line', '<path d="M 10 40 '+' '.join(f'L {x} 40' for x in range(11, 71))+'" fill="none" stroke="gray" stroke-width="2"/>'),
])
def test_redundant_geometry_has_one_simpler_native_form_candidate(kind, body):
    seed = scene(body)
    proposals = [s for s, origin in simplification_proposals(seed) if origin == 'simplify:'+kind]
    assert proposals
    for svg in proposals:
        assert representation_cost(svg)['penalty'] < representation_cost(seed)['penalty']
        assert np.mean(abs(render_svg(svg, 80, 80).astype(float)-render_svg(seed, 80, 80))) < 1
        assert len(list(ET.fromstring(svg))) == 2


@pytest.mark.parametrize('description,bad', [
    ('Eine Gerade.', ''.join(f'<line x1="{x}" y1="40" x2="{x+2}" y2="{40+(x%3)}" stroke="gray"/>' for x in range(10, 50, 2))),
    ('Ein Kreis.', ''.join(f'<circle cx="{x}" cy="40" r="2"/>' for x in range(10, 50, 2))),
    ('Ein Rechteck.', ''.join(f'<rect x="{x}" y="30" width="2" height="10"/>' for x in range(10, 50, 2))),
    ('Ein Dreieck.', ''.join(f'<polygon points="{x},30 {x+2},34 {x-2},34"/>' for x in range(10, 50, 2))),
])
def test_one_described_object_cannot_be_twenty_native_patches(description, bad):
    for assertions in (description_assertions(description), draft_assertions(description_assertions(description))):
        with pytest.raises(ValueError, match='logical_object_count'):
            validate_svg_assertions(scene(bad), assertions)


def test_continuous_polyline_is_not_misread_as_one_straight_object():
    svg = scene('<polyline points="10,40 20,39 30,42 40,38 50,40" stroke="gray" fill="none"/>')
    with pytest.raises(ValueError, match='logical_object_count:line:1:'):
        validate_svg_assertions(svg, description_assertions('Eine Gerade.'))
    validate_svg_assertions(scene('<path d="M 10 40 L 50 40" fill="none" stroke="gray"/>'),
                            description_assertions('Eine Gerade.'))


def test_identical_render_simplification_is_real_progress():
    seed = scene('<path d="M 10 40 L 20 40 L 30 40 L 40 40 L 60 40" fill="none" stroke="gray" stroke-width="2"/>')
    target = render_svg(seed, 80, 80)[:, :, ::-1].copy()
    def render(svg, w, h):
        return render_svg(svg, w, h)[:, :, ::-1].copy()
    session = ImageSearch(SearchPolicy(seconds=3, max_seconds=3))
    with image_search(session):
        result, report = explore_structures(seed, target, target, render, session, {}, max_probes=1)
    assert report['proposals'][0]['accepted']
    assert result['error'] == 0 and result['origin'] == 'simplify:line'
    assert '<path' not in result['svg'] and '<line' in result['svg']


@pytest.mark.parametrize('kind', ['rect', 'circle', 'ellipse', 'polygon', 'line'])
def test_many_same_paint_fragments_offer_one_complete_form(kind):
    if kind == 'rect':
        body = ''.join(f'<rect x="{10+i*3}" y="15" width="3" height="45" fill="#668899"/>' for i in range(20))
    elif kind == 'line':
        body = ''.join(f'<line x1="{10+i*3}" y1="40" x2="{13+i*3}" y2="40" stroke="#668899" stroke-width="2"/>' for i in range(20))
    else:
        if kind == 'polygon':
            boundary = densify(np.array([[40, 12], [65, 65], [15, 65]]))
        else:
            t = np.linspace(0, 2*np.pi, 80, endpoint=False)
            boundary = np.c_[40+25*np.cos(t), 40+(25 if kind == 'circle' else 18)*np.sin(t)]
        body = ''.join(polygon(np.array([[40, 40], a, b])) for a, b in zip(boundary, np.roll(boundary, -1, axis=0)))
    seed = scene(body)
    proposals = list(simplification_proposals(seed))
    matching = [s for s, _ in proposals if len([n for n in ET.fromstring(s) if n.tag.rsplit('}', 1)[-1] == kind])
                >= (2 if kind == 'rect' else 1) and len(list(ET.fromstring(s))) == 2]
    assert matching, kind
    assert min(representation_cost(s)['penalty'] for s in matching) < representation_cost(seed)['penalty']*.25


def test_fragmented_template_can_be_rebuilt_without_publishing_more_fragments(tmp_path):
    from PIL import Image
    from src.imageConverterSample import refine
    source_svg = scene('<rect x="10" y="15" width="60" height="45" fill="#668899"/>')
    seed = scene(''.join(f'<rect x="{10+i*3}" y="15" width="3" height="45" fill="#668899"/>' for i in range(20)))
    source, sample, output = (tmp_path/name for name in ('neutral.png', 'template.svg', 'result.svg'))
    Image.fromarray(render_svg(source_svg, 80, 80)).save(source)
    sample.write_text(seed)
    report = refine(source, sample, output, 'Ein Rechteck.', 3., seed=17)
    assert report['passed'] and report['continuation']
    validate_svg_assertions(output.read_text(), description_assertions('Ein Rechteck.'))
    assert len(list(ET.parse(output).getroot())) == 2


def test_overcomplete_seed_can_be_repaired_stepwise_without_claiming_acceptance():
    body = '<rect x="10" y="15" width="60" height="45" fill="#668899"/>'
    target_svg = scene(body)
    seed = scene(body+'<rect x="2" y="2" width="5" height="5" fill="red"/>'
                 '<rect x="72" y="72" width="5" height="5" fill="red"/>')
    target = render_svg(target_svg, 80, 80)[:, :, ::-1].copy()
    def render(svg, w, h):
        return render_svg(svg, w, h)[:, :, ::-1].copy()
    full = description_assertions('Ein Rechteck.')
    session = ImageSearch(SearchPolicy(seconds=3, max_seconds=3))
    with image_search(session):
        result, report = explore_structures(seed, target, render(seed, 80, 80), render, session,
                                            draft_assertions(full), level=1, max_probes=1)
    assert report['proposals'][0]['partial_object_repair']
    assert report['proposals'][0]['accepted']
    assert representation_cost(result['svg'])['elements'] < representation_cost(seed)['elements']
    with pytest.raises(ValueError, match='logical_object_count'):
        validate_svg_assertions(result['svg'], full)


def test_quantities_and_negative_clauses_are_kept_separate():
    assert description_assertions('Zwei Diagonalen und ein Quadrat in einem schmalen Rechteck.')['objects'] == {'diagonal': 2, 'square': 1, 'rect': 1}
    assert not description_assertions('ohne einen Kreis').get('objects')
    assert not description_assertions('Eine gerade Kante.').get('objects')


def test_declared_plus_minus_bars_are_parts_of_symbols_not_extra_full_lines():
    svg = scene('<rect x="5" y="5" width="70" height="70" fill="#eeeeee" stroke="gray"/>'
        '<line x1="5" y1="5" x2="75" y2="75" stroke="gray"/>'
        '<line x1="75" y1="5" x2="5" y2="75" stroke="gray"/>'
        '<rect x="35" y="12" width="10" height="2" fill="gray"/>'
        '<rect x="39" y="8" width="2" height="10" fill="gray"/>'
        '<rect x="35" y="22" width="10" height="2" fill="gray"/>')
    validate_svg_assertions(svg, description_assertions('Ein Rechteck mit zwei diagonalen Geraden. Oben ein Pluszeichen und ein Minuszeichen.'))


def test_backing_is_not_confused_with_a_frame_and_transformed_field_has_one_border():
    validate_svg_assertions(scene('<rect x=".5" y=".5" width="79" height="79" fill="none" stroke="gray"/>'),
                            description_assertions('Ein Rechteck.'))
    svg = scene('<g transform="translate(10 10) scale(5)"><rect width="10" height="10" fill="#668899"/></g>'
                '<rect x="10" y="10" width="50" height="50" fill="none" stroke="gray"/>')
    validate_svg_assertions(svg, description_assertions('Ein Rechteck.'))


@pytest.mark.parametrize('shape', [
    '<rect x="10" y="10" width="20" height="20" fill="none" stroke="gray"/>',
    '<polygon points="20,10 30,20 20,30 10,20" fill="none" stroke="gray"/>',
])
def test_stretched_square_is_checked_in_displayed_coordinates(shape):
    valid = scene('<g transform="translate(5 7) rotate(20) scale(1.1)">'+shape+'</g>')
    validate_svg_assertions(valid, description_assertions('Ein Quadrat.'))
    stretched = scene('<g transform="scale(1.6 .8)">'+shape+'</g>')
    with pytest.raises(ValueError, match='logical_object_count:square:1:0'):
        validate_svg_assertions(stretched, description_assertions('Ein Quadrat.'))


def test_nonuniform_scaling_changes_circle_and_ellipse_roles():
    oval = scene('<g transform="scale(1.5 .7)"><circle cx="25" cy="40" r="12"/></g>')
    validate_svg_assertions(oval, description_assertions('Eine Ellipse.'))
    with pytest.raises(ValueError, match='logical_object_count:circle:1:0'):
        validate_svg_assertions(oval, description_assertions('Ein Kreis.'))
    circle = scene('<g transform="scale(2 1)"><ellipse cx="20" cy="40" rx="8" ry="16"/></g>')
    validate_svg_assertions(circle, description_assertions('Ein Kreis.'))
