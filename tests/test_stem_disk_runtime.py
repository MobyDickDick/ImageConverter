"""Circle rim raster noise must not become a second handle or a tangent line."""
from pathlib import Path
from xml.etree import ElementTree as ET

import cv2
import numpy as np
import pytest

from src.iCCModules.imageCompositeConverterStemDisk import fit_stem_disk
from src.iCCModules.imageCompositeConverterSearchPortfolio import search_configuration, configured_image_search
from tools.run_plan_b_variations import render, measure_quality

ROOT = Path(__file__).resolve().parents[1]
DESCRIPTION = ('Wie AC0811: Kelle, ohne Text Kreis oben, Griff nach links (dunkelgraue Liine). '
               'Der Griff liegt auf einer Symmetrieachse des Kreises.')


def fit(image, description=DESCRIPTION):
    h, w = image.shape[:2]
    return fit_stem_disk(w, h, description=description, image=image, render_fn=render,
                         error_fn=lambda a, b: float(np.square(a.astype(float)-b).mean()/255**2))


def assert_topology(svg, direction):
    root = ET.fromstring(svg)
    tags = [node.tag.rsplit('}', 1)[-1] for node in root.iter()]
    assert sorted(tags) == sorted(['svg', 'rect', 'line', 'circle'])
    line = next(e for e in root if e.tag.endswith('line'))
    circle = next(e for e in root if e.tag.endswith('circle'))
    cx, cy, r = [float(circle.get(k)) for k in ['cx', 'cy', 'r']]
    x1, y1, x2, y2 = [float(line.get(k)) for k in ['x1', 'y1', 'x2', 'y2']]
    assert (x2, y2) == (cx, cy)
    if direction in ['links', 'rechts']:
        assert y1 == cy
        assert x1 < cx-r if direction == 'links' else x1 > cx+r
    else:
        assert x1 == cx
        assert y1 < cy-r if direction == 'oben' else y1 > cy+r


@pytest.mark.parametrize('size', ['S', 'M', 'L'])
def test_original_sizes_keep_exactly_one_axial_handle(size):
    image = cv2.imread(str(ROOT/f'artifacts/images_to_convert/AC0812_{size}.jpg'))
    original = image.copy()
    result = fit(image)
    assert result is not None
    assert_topology(result['svg'], 'links')
    assert measure_quality(image, result['svg'])['satisfactory']
    np.testing.assert_array_equal(image, original)


def synthetic(scale=1, body='', line=''):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{90*scale}" height="{64*scale}" viewBox="0 0 90 64">'
            '<rect width="90" height="64" fill="white"/>'
            +(line or '<line x1="7" y1="30" x2="57" y2="30" stroke="#486a78" stroke-width="2.5"/>')
            +'<circle cx="57" cy="30" r="24" fill="#d8e8ec" stroke="#597582" stroke-width="1.5"/>'
            +body+'</svg>')


@pytest.mark.parametrize('turns,direction', [(0,'links'), (1,'unten'), (2,'rechts'), (3,'oben')])
@pytest.mark.parametrize('scale', [.5, 1, 2])
def test_independent_color_geometry_size_and_all_axes(turns, direction, scale):
    image = np.rot90(render(synthetic(scale), int(90*scale), int(64*scale)), turns).copy()
    result = fit(image, f'Ein unbeschrifteter Kreis mit einem geraden Griff nach {direction}.')
    assert result is not None
    assert_topology(result['svg'], direction)
    assert measure_quality(image, result['svg'])['satisfactory']


@pytest.mark.parametrize('body,line', [
    ('<circle cx="56" cy="30" r="2" fill="black"/>', ''),
    ('<circle cx="7" cy="7" r="2" fill="black"/>', ''),
    ('', '<line x1="7" y1="36" x2="57" y2="36" stroke="#486a78" stroke-width="2.5"/>'),
    ('', '<line x1="7" y1="30" x2="27" y2="30" stroke="#486a78" stroke-width="2.5"/>'),
    ('', '<line x1="7" y1="30" x2="57" y2="30" stroke="#486a78" stroke-width="15"/>'),
])
def test_missing_detached_off_axis_or_extra_objects_reject(body, line):
    assert fit(render(synthetic(body=body, line=line),90,64)) is None


@pytest.mark.parametrize('extra', [' Zusätzlich ein Punkt.', ' Text im Kreis: "Q".', ' Ohne Griff.', ' Ein zweiter Griff.'])
def test_additional_description_content_is_not_discarded(extra):
    assert fit(render(synthetic(),90,64), DESCRIPTION+extra) is None


def test_adaptive_search_keeps_same_topology():
    image = cv2.imread(str(ROOT/'artifacts/images_to_convert/AC0812_L.jpg'))
    with search_configuration(mode='portfolio', seed=3346729347937762982, adaptive=True,
                              minimum_seconds=30, seconds=35, max_seconds=45):
        with configured_image_search('neutral'):
            result = fit(image)
    assert result is not None
    assert_topology(result['svg'], 'links')


def test_saved_model_contract_rejects_a_second_line_even_if_pixels_pass():
    from types import SimpleNamespace
    from src.iCCModules.imageCompositeConverterDescriptionLanguage import DescriptionRejected
    from src.iCCModules.imageCompositeConverterIterationInitialization import prepareIterationRuntimeImpl

    saved = []
    params = dict(language_assertions=dict(no_text=True, counts=[]))
    setup = SimpleNamespace(emitIterationDescriptionHeaderImpl=lambda **kw: None,
        ensureIterationOutputDirsImpl=lambda **kw: None,
        buildIterationBaseAndLogPathImpl=lambda **kw: ('neutral', 'unused.log'))
    runtime = SimpleNamespace(buildIterationArtifactCallbacksImpl=lambda **kw: dict(
        write_attempt_artifacts=lambda *args, **kw: saved.append(args)))
    state = prepareIterationRuntimeImpl(filename='neutral.png', params=params,
        reports_out_dir=None, svg_out_dir='unused', diff_out_dir='unused', target_img=None,
        width=90, height=64, run_seed=0, pass_seed_offset=0, iteration_setup_helpers=setup,
        iteration_runtime_helpers=runtime, time_ns_fn=lambda: 0,
        render_svg_to_numpy_fn=lambda *args: None, create_diff_image_fn=None, cv2_module=None)
    # Registration happens after the output callbacks have been created.
    params['stem_disk_registration'] = dict(source='stem_disk_v1')
    writer = state['artifact_callbacks']['write_attempt_artifacts']
    writer(synthetic())
    with pytest.raises(DescriptionRejected, match='object_count:line:1:2'):
        writer(synthetic(body='<line x1="34" y1="48" x2="40" y2="53" stroke="gray"/>'))
    assert len(saved) == 1
