from pathlib import Path
from xml.etree import ElementTree as ET
import json

import numpy as np
import pytest

from src.iCCModules.imageCompositeConverterAxialPanel import fit_axial_panel, panel_contract
from src.iCCModules.imageCompositeConverterDescriptions import loadDescriptionMappingImpl
from src.iCCModules.imageCompositeConverterNaming import getBaseNameFromFileImpl
from tools.run_plan_b_variations import render, measure_quality, select_task
from tools.evaluate_axial_panel import independent_cases
from src.iCCModules.imageCompositeConverterAdaptiveSearch import ImageSearch, SearchPolicy, image_search


def fit(case, image=None):
    image = render(case['svg'], case['width'], case['height']) if image is None else image
    return fit_axial_panel(case['width'], case['height'], description=case['description'], image=image,
                           render_fn=render, error_fn=lambda a, b: float(np.mean((a.astype(float)-b)**2)))


@pytest.mark.parametrize('case', list(independent_cases()))
def test_foreign_colors_sizes_axes_preserve_one_native_continuous_rectangle(case):
    result = fit(case)
    assert result is not None
    root = ET.fromstring(result['svg'])
    assert len(root.findall('{*}rect')) == 1
    assert not root.findall('.//{*}path') and not root.findall('.//{*}image')
    assert len(root.findall('.//{*}stop')) <= 4
    assert measure_quality(render(case['svg'], case['width'], case['height']), result['svg'])['satisfactory']
    rect = root.find('{*}rect')
    assert abs(float(rect.get('x'))-4) < .2 and abs(float(rect.get('y'))-3) < .2
    assert result['evaluations'] <= 5
    assert result['hypotheses'][0]['stops'] == 2
    # Production checkpoints save these diagnostics after a successful fit.
    json.dumps({k: v for k, v in result.items() if k not in {'svg', 'rendered'}})


@pytest.mark.parametrize('extra', [' Ein Kreis.', ' Mit Text.', ' Nicht ohne Kontur.',
                                   ' Eine zweite Fläche.', ' Mit radialem Farbverlauf.',
                                   ' Der Verlauf ist umgekehrt.'])
def test_unconsumed_claims_decline_plain_panel(extra):
    assert panel_contract(next(independent_cases())['description']+extra) is None


@pytest.mark.parametrize('damage', ['solid', 'wrong_axis', 'wrong_color', 'extra_mark', 'split'])
def test_plain_panel_does_not_accept_wrong_shape_or_paint(damage):
    case = next(c for c in independent_cases() if c['width'] > c['height'])
    image = render(case['svg'], case['width'], case['height'])
    if damage == 'solid':
        image[3:-3, 4:-4] = [160, 100, 60]
    elif damage == 'wrong_axis':
        image = image[::-1].transpose(1, 0, 2).copy()
        case = dict(case, width=case['height'], height=case['width'])
    elif damage == 'wrong_color':
        image = image[:, :, ::-1].copy()
    elif damage == 'extra_mark':
        image[4:7, 15:30] = 0
    elif damage == 'split':
        image[:, 30:34] = 255
    assert fit(case, image) is None


def test_catalog_and_random_pool_have_the_standalone_description(tmp_path):
    root = Path(__file__).resolve().parents[1]
    catalog = root/'artifacts/images_to_convert/Finale_Wurzelformen_V3.xml'
    mapping = loadDescriptionMappingImpl(str(catalog), get_base_name_from_file_fn=getBaseNameFromFileImpl)
    description = mapping['z_201']
    assert description.startswith('Ein einzelnes') and 'T-Stücke' not in description
    (tmp_path/'z_201.svg').write_bytes((root/'artifacts/samples/z_201.svg').read_bytes())
    assert select_task(tmp_path, catalog, 1)[1] == description
    assert panel_contract(description) is not None


@pytest.mark.parametrize('damage', ['reverse', 'no_highlight', 'no_pink_recovery'])
def test_declared_pink_zones_cannot_be_silently_discarded(damage):
    root = Path(__file__).resolve().parents[1]
    catalog = root/'artifacts/images_to_convert/Finale_Wurzelformen_V3.xml'
    desc = loadDescriptionMappingImpl(str(catalog), get_base_name_from_file_fn=getBaseNameFromFileImpl)['z_201']
    svg = (root/'artifacts/samples/z_201.svg').read_text(encoding='utf-8')
    image = render(svg, 510, 50)
    if damage == 'reverse':
        image = image[::-1].copy()
    elif damage == 'no_highlight':
        for channel, (start, end) in enumerate([(190, 130), (190, 125), (245, 220)]):
            image[:, :, channel] = np.linspace(start, end, 50)[:, None]
    else:
        image[-1] = image[-2]
    assert fit(dict(svg=svg, width=510, height=50, description=desc), image) is None


def test_expired_image_budget_prevents_panel_renders():
    case = next(independent_cases())
    image = render(case['svg'], case['width'], case['height'])
    session = ImageSearch(SearchPolicy(), clock=lambda: 0)
    session.spent = 120
    def forbidden_render(*args):
        raise AssertionError('Expired image search must not render')
    with image_search(session):
        assert fit_axial_panel(case['width'], case['height'], description=case['description'], image=image,
                               render_fn=forbidden_render, error_fn=lambda a, b: 0) is None
