from pathlib import Path
from xml.etree import ElementTree as ET

import cv2
import numpy as np
import pytest

from src.iCCModules.imageCompositeConverterAdaptiveSearch import ImageSearch, SearchPolicy, image_search
from src.iCCModules.imageCompositeConverterFramedPanel import fit_framed_panel, panel_contract, profile_quality
from tools.run_plan_b_variations import render

ROOT = Path(__file__).resolve().parents[1]
DESCRIPTION = ('Liegendes Rechteck mit Farbverlauf in vertikaler Richtung und dunkelgrauer Umrandung. '
               'Der Farbverlauf ist von oben nach unten grau / fast weiss / fast weiss / grau. '
               'Die zwei fast-weissen Bereiche deuten auf ein kleines helles, horizontales Band hin; '
               'der helle Bereich liegt oberhalb der Mitte.')


def fit(image, description=DESCRIPTION, **kwargs):
    return fit_framed_panel(image.shape[1], image.shape[0], description=description, image=image,
        render_fn=kwargs.get('render_fn', render),
        error_fn=kwargs.get('error_fn', lambda a, b: float(np.mean((a.astype(float)-b)**2))))


def test_actual_jpeg_preserves_highlight_and_refines_instead_of_accepting_coarse_fallback():
    from src.iCCModules.imageCompositeConverterNonCompositeRuntime import _try_build_plain_framed_panel_svg
    image = cv2.imread(str(ROOT/'artifacts/images_to_convert/AC0VR2_M.jpg'))
    old = render(_try_build_plain_framed_panel_svg(60, 30, description=DESCRIPTION, perc_img=image), 60, 30)
    assert not profile_quality(image, old, 1, (0, 0, 60, 30))['passed']
    session = ImageSearch(SearchPolicy())
    with image_search(session):
        result = fit(image)
    assert result is not None and result['profile_quality']['passed']
    assert result['error'] < np.mean((image.astype(float)-old)**2)*.1
    assert session.evaluations > 1
    root = ET.fromstring(result['svg'])
    assert len(root.findall('{*}rect')) == 1 and len(root.findall('.//{*}stop')) == 4
    assert not root.findall('.//{*}image') and not root.findall('.//{*}path')


def synthetic(axis, scale):
    # Unrelated paint, highlight location, aspect ratio, padding and resolution.
    coords = 'x1="0" x2="0" y1="0" y2="1"' if axis else 'y1="0" y2="0" x1="0" x2="1"'
    w, h = (76, 38) if axis else (38, 76)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w*scale}" height="{h*scale}" viewBox="0 0 {w} {h}">'
           f'<defs><linearGradient id="foreign" {coords}>'
           '<stop offset="0" stop-color="#999999"/><stop offset=".28" stop-color="#f4f4f4"/>'
           '<stop offset=".43" stop-color="#f4f4f4"/><stop offset="1" stop-color="#bbbbbb"/>'
           '</linearGradient></defs>'
           f'<rect x="3.5" y="3.5" width="{w-7}" height="{h-7}" fill="url(#foreign)" stroke="#808080"/></svg>')
    description = (f'{"Liegendes" if axis else "Stehendes"} Rechteck mit Farbverlauf in '
                   f'{"vertikaler" if axis else "horizontaler"} Richtung und dunkelgrauer Umrandung. '
                   f'Der Farbverlauf ist von {"oben nach unten" if axis else "links nach rechts"} '
                   'grau / fast weiss / fast weiss / grau.')
    return render(svg, w*scale, h*scale), description


@pytest.mark.parametrize('axis', [0, 1])
@pytest.mark.parametrize('scale', [1, 2, 3])
def test_other_sizes_padding_axes_and_paints(axis, scale):
    image, description = synthetic(axis, scale)
    result = fit(image, description)
    assert result is not None and result['profile_quality']['passed']


@pytest.mark.parametrize('damage', ['mark', 'color', 'flat', 'reverse'])
def test_unsupported_raster_claims_are_rejected(damage):
    image = cv2.imread(str(ROOT/'artifacts/images_to_convert/AC0VR2_M.jpg'))
    if damage == 'mark':
        image[8:18, 20:35] = 30
    elif damage == 'color':
        image[:, :, 0] = 10
    elif damage == 'flat':
        image[1:-1, 1:-1] = 225
    else:
        image = image[::-1].copy()
    assert fit(image) is None


def test_contract_render_error_and_budget_guards():
    image = cv2.imread(str(ROOT/'artifacts/images_to_convert/AC0VR2_M.jpg'))
    assert panel_contract(DESCRIPTION+' Ein Kreis.') is None
    assert fit(image, render_fn=lambda *args: None) is None
    assert fit(image, error_fn=lambda *args: float('nan')) is None
    session = ImageSearch(SearchPolicy(), clock=lambda: 0)
    session.spent = 120
    with image_search(session):
        assert fit(image, render_fn=lambda *args: pytest.fail('Expired search rendered')) is None


def test_neutral_gui_upload_runs_registered_model_and_saved_result_check(tmp_path):
    import os
    import shutil
    import subprocess
    import sys
    from PIL import Image
    from src.imageConverterGui import collect_result, write_description_table

    inputs = tmp_path/'input'
    inputs.mkdir()
    source = ROOT/'artifacts/images_to_convert/AC0VR2_M.jpg'
    shutil.copyfile(source, inputs/'UPLOAD.jpg')
    with Image.open(source) as image:
        image.save(tmp_path/'source.png')
    write_description_table(tmp_path/'description.csv', DESCRIPTION, {})
    environment = os.environ.copy()
    environment.update(IMAGE_CONVERTER_ISOLATE_SVG_RENDER='1', IMAGE_CONVERTER_REUSE_RENDER_WORKER='1',
                       ICC_MAX_QUALITY_PASSES='0', ICC_CONVERSION_TIMEOUT_SEC='120')
    completed = subprocess.run([sys.executable, '-m', 'src.imageCompositeConverter', str(inputs),
        '--descriptions-path', str(tmp_path/'description.csv'), '--output-dir', str(tmp_path/'output'),
        '--start', 'UPLOAD', '--end', 'UPLOAD', '--execution-mode', 'semantic-only',
        '--search-seconds', '60', '--search-max-seconds', '120', '--search-seed', '75231',
        '--log-file', str(tmp_path/'converter.local.log'), '--fail-on-batch-failures'],
        cwd=ROOT, env=environment, capture_output=True, timeout=40)
    assert completed.returncode == 0, completed.stdout.decode(errors='replace')
    job = {}
    collect_result(tmp_path, job, completed.returncode)
    assert job['quality'] == 'passed' and job['pixel_quality']['passed']
    assert job['search_summary']['satisfactory']
    assert job['search_summary']['candidate_evaluations'] > 1
    assert 'framed_axial_panel' in completed.stdout.decode(errors='replace')
