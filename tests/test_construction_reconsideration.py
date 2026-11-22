"""A failed fit must yield to genuinely different, reproducible constructions."""
from pathlib import Path
from xml.etree import ElementTree as ET

import cv2
import numpy as np
import pytest

from src.iCCModules.imageCompositeConverterAdaptiveSearch import ImageSearch, SearchPolicy, image_search, pixel_quality
from src.iCCModules.imageCompositeConverterConstructionVariants import construction_variants
from src.iCCModules.imageCompositeConverterFilledSymbols import _register
from src.iCCModules.imageCompositeConverterFallbackStructure import explore_structures
from src.iCCModules.imageCompositeConverterRuledPanel import fit_ruled_panel
from src.iCCModules.imageCompositeConverterSearchPortfolio import search_configuration, configured_image_search
from src.imageConverterSample import render_svg

ROOT = Path(__file__).resolve().parents[1]
DESCRIPTION = ('Graues Rechteck hochkant, graue Umrandung, drei graue horizontale Linien, '
               'horizontaler Farbverlauf dunkel-hell-dunkel. Die hellste Stelle liegt bei 40% vom linken Rand.')


def render(svg, w, h):
    return render_svg(svg, w, h)[:, :, ::-1].copy()


def error(a, b):
    return float(np.square(a.astype(float)-b.astype(float)).mean()/255**2)


def test_failed_parameter_fit_yields_before_the_deadline_for_other_constructions():
    reference = np.zeros((16, 16, 3), dtype=np.uint8)
    now = [0.]
    def bad_render(svg, w, h):
        now[0] += .001
        return np.full_like(reference, 255)
    with search_configuration(mode='portfolio', adaptive=True, seed=7, budget=384,
                              seconds=10, max_seconds=10, minimum_seconds=10):
        with configured_image_search('impossible') as session:
            session.clock, session.active_since = lambda: now[0], 0.
            fitted = _register([1.], 1, lambda p: '<svg value="'+str(p[0])+'"/>',
                               lambda p: True, reference, bad_render, error, 'native_svg_continuation',
                               satisfactory_fn=lambda p, m: False, reconsider_after=12)
    assert fitted['search_control']['stop_reason'] == 'structure_reconsideration'
    assert 12 <= fitted['evaluations'] <= 16
    assert fitted['search_control']['elapsed_seconds'] < 1.
    assert session.time_reason() is None and not session.validated


def test_seed_changes_construction_order_and_same_seed_replays_without_duplicates():
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="60" height="80">'
           '<defs><linearGradient id="g" x1="0" x2="0" y1="0" y2="1">'
           '<stop offset="0" stop-color="#dddddd"/><stop offset="1" stop-color="#555555"/>'
           '</linearGradient></defs><rect width="60" height="80" fill="white"/>'
           '<rect x="20" y="10" width="20" height="60" fill="url(#g)"/>'
           '<line x1="22" x2="38" y1="25" y2="27" stroke="black"/></svg>')
    target = render(svg.replace('x="20"', 'x="5"').replace('width="20"', 'width="50"'), 60, 80)
    initial = render(svg, 60, 80)
    def sequence(seed):
        with search_configuration(seed=seed):
            session = ImageSearch(SearchPolicy())
            values = list(construction_variants(svg, target, initial, session))
            assert not list(construction_variants(svg, target, initial, session))
            return values
    assert sequence(7) == sequence(7)
    assert len({tuple(label for _, label in sequence(seed)) for seed in range(5)}) > 1
    labels = {label for _, label in sequence(7)}
    assert 'construction_variant:aligned_lines' in labels
    assert any(label.startswith('construction_variant:raster_bounds:') for label in labels)
    def probes(seed):
        with search_configuration(seed=seed):
            session = ImageSearch(SearchPolicy())
            with image_search(session):
                _, report = explore_structures(svg, target, initial, render, session, {}, max_probes=2)
            return [(p['origin'], p.get('error')) for p in report['proposals']]
    assert probes(7) == probes(7)
    assert len({tuple(probes(seed)) for seed in range(5)}) > 1


@pytest.mark.parametrize('axis,count', [(0, 1), (0, 4), (1, 2)])
def test_measured_panel_supports_other_sizes_counts_and_both_axes(axis, count):
    w, h = (64, 96) if axis == 0 else (96, 64)
    gradient = 'x1="0" x2="1" y1="0" y2="0"' if axis == 0 else 'x1="0" x2="0" y1="0" y2="1"'
    marks = ''
    for position in np.linspace(18, 76, count) if count > 1 else [47]:
        coords = (12, position, 52, position) if axis == 0 else (position, 12, position, 52)
        marks += '<line '+ ' '.join(f'{k}="{v}"' for k,v in zip(('x1','y1','x2','y2'),coords))+' stroke="#777777" stroke-width="3"/>'
    x, y, rw, rh = (4.5, 5.5, 55, 84) if axis == 0 else (5.5, 4.5, 84, 55)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}">'
           f'<defs><linearGradient id="g" {gradient}><stop offset="0" stop-color="#bbbbbb"/>'
           '<stop offset=".4" stop-color="#fafafa"/><stop offset="1" stop-color="#bbbbbb"/></linearGradient></defs>'
           f'<rect width="{w}" height="{h}" fill="white"/><rect x="{x}" y="{y}" width="{rw}" height="{rh}" '
           f'fill="url(#g)" stroke="#888888" stroke-width="1"/>{marks}</svg>')
    source = render(svg, w, h)
    description = f'Graues Rechteck mit grauem Rand und Farbverlauf. {count} graue '+('horizontale' if axis == 0 else 'vertikale')+' Linien.'
    fitted = fit_ruled_panel(w, h, description=description, image=source, render_fn=render, error_fn=error)
    assert fitted and pixel_quality(source, fitted['rendered'])['passed']
    assert fitted['mark_count'] == count and fitted['gradient_axis'] == axis
    assert fit_ruled_panel(w, h, description=description.replace(str(count)+' graue', '8 graue'),
                          image=source, render_fn=render, error_fn=error) is None


def test_ac0110_description_refit_replaces_bad_axis_and_sloping_marks(tmp_path):
    source = ROOT/'artifacts/images_to_convert/AC0110.jpg'
    # Deliberately wrong proportions, gradient axis, number and length of marks.
    seed = tmp_path/'wrong.svg'
    seed.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="40" height="80">'
                    '<defs><linearGradient id="g" x1="0" x2="0" y1="0" y2="1">'
                    '<stop offset="0" stop-color="#dddddd"/><stop offset="1" stop-color="#bbbbbb"/>'
                    '</linearGradient></defs><rect width="40" height="80" fill="white"/>'
                    '<rect x="13" y="8" width="14" height="60" fill="url(#g)"/>'
                    '<line x1="14" y1="30" x2="25" y2="28" stroke="#777777"/></svg>')
    output = tmp_path/'result.svg'
    from src.imageConverterSample import refine
    report = refine(source, seed, output, DESCRIPTION, 12., seed=7)
    assert report['passed'] and report['restarted_from_description'], report
    assert report['elapsed'] < 12.5
    image = cv2.imread(str(source))
    assert pixel_quality(image, render(output.read_text(), 40, 80))['passed']
    root = ET.parse(output).getroot()
    gradient = next(n for n in root.iter() if n.tag.endswith('linearGradient'))
    assert gradient.get('y1') == gradient.get('y2')
    lines = [n for n in root.iter() if n.tag.endswith('line')]
    assert len(lines) == 3 and all(n.get('y1') == n.get('y2') for n in lines)
    assert not any(n.tag.rsplit('}',1)[-1] in {'image','path','text'} for n in root.iter())
