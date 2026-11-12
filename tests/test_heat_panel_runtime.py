from pathlib import Path
from xml.etree import ElementTree as ET

import cv2
import numpy as np
import pytest

from src.iCCModules.imageCompositeConverterAdaptiveSearch import ImageSearch, SearchPolicy, image_search, pixel_quality
from src.iCCModules.imageCompositeConverterHeatPanel import fit_heat_panel
from tools.run_plan_b_variations import render


ROOT = Path(__file__).resolve().parents[1]
DESCRIPTION = ('Heizelement, graues Rechteck, Plus-Minus-Zeichen oben links, '
               'Farbverlauf horizontal dunkel-hell-dunkel graue Diagonale oben rechts nach unten links')


def fit(image, description=DESCRIPTION, render_fn=render):
    return fit_heat_panel(image.shape[1], image.shape[0], description=description, image=image,
                          render_fn=render_fn,
                          error_fn=lambda a, b: float(np.mean((a.astype(float)-b)**2)))


def synthetic(scale=1, minus=False):
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{60*scale}" height="{90*scale}" viewBox="0 0 60 90">'
           '<defs><linearGradient id="g"><stop offset="0" stop-color="#bcbcbc"/>'
           '<stop offset=".5" stop-color="#fafafa"/><stop offset="1" stop-color="#bcbcbc"/></linearGradient></defs>'
           '<rect width="60" height="90" fill="white"/>'
           '<rect x="5" y="6" width="50" height="78" fill="url(#g)" stroke="#888888"/>'
           '<path d="M 54 7 L 6 83" stroke="#777777" stroke-width="2"/>'
           '<path d="M 12 18 H 22 M 17 13 V 23" stroke="#666666" stroke-width="2"/>'
           + ('<path d="M 27 18 H 35" stroke="#666666" stroke-width="2"/>' if minus else '')+'</svg>')
    return render(svg, 60*scale, 90*scale)


@pytest.mark.parametrize('catalog_description', [False, True])
def test_actual_jpeg_preserves_plus_instead_of_inventing_minus(catalog_description):
    image = cv2.imread(str(ROOT/'artifacts/images_to_convert/AC0010.jpg'))
    description = DESCRIPTION
    if catalog_description:
        from src.imageConverterGui import catalog_descriptions
        description = catalog_descriptions()['AC0010']
        assert 'Pluszeichen' in description and 'Kein separates Minuszeichen' in description
    result = fit(image, description)
    assert result is not None and pixel_quality(image, result['rendered'])['passed']
    assert result['observed_glyphs'] == ['plus']
    root = ET.fromstring(result['svg'])
    assert len(root.findall('{*}path')) == 1
    assert len(root.findall('{*}line')) == 1
    assert len(root.findall('.//{*}stop')) == 5
    assert not root.findall('.//{*}image')
    # Both arms survive at the measured source location, far from the old seed.
    assert result['rendered'][12, 10:18].mean() < 170
    assert result['rendered'][9:16, 13].mean() < 170


@pytest.mark.parametrize('scale', [1, 2, 3])
@pytest.mark.parametrize('minus', [False, True])
def test_independent_geometry_at_multiple_sizes(scale, minus):
    image = synthetic(scale, minus)
    result = fit(image)
    assert result is not None and pixel_quality(image, result['rendered'])['passed']
    assert result['observed_glyphs'] == (['plus', 'minus'] if minus else ['plus'])


@pytest.mark.parametrize('damage', ['missing_plus', 'extra_object', 'colored', 'explicit_missing_minus', 'wrong_diagonal'])
def test_missing_or_unexplained_objects_are_rejected(damage):
    image = synthetic()
    description = DESCRIPTION
    if damage == 'missing_plus':
        image[11:25, 10:24] = 225
    elif damage == 'extra_object':
        image[55:61, 38:44] = 30
    elif damage == 'colored':
        image[:, :, 0] = 0
    elif damage == 'explicit_missing_minus':
        description = DESCRIPTION.replace('Plus-Minus-Zeichen', 'Plus und Minus')
    else:
        description = DESCRIPTION.replace('oben rechts nach unten links', 'oben links nach unten rechts')
    assert fit(image, description) is None


def test_expired_budget_never_renders():
    session = ImageSearch(SearchPolicy(seconds=1, max_seconds=1))
    session.spent = 2
    with image_search(session):
        assert fit(synthetic(), render_fn=lambda *a: pytest.fail('expired budget')) is None


@pytest.mark.parametrize('seed', [42, 314159])
def test_real_gui_cli_accepts_saved_vector_under_neutral_upload_name(tmp_path, seed, monkeypatch):
    import shutil
    import subprocess
    import sys
    from PIL import Image
    from src.imageConverterGui import collect_result, write_description_table
    monkeypatch.setenv('IMAGE_CONVERTER_REUSE_RENDER_WORKER', '1')
    inputs = tmp_path/'input'
    inputs.mkdir()
    source = ROOT/'artifacts/images_to_convert/AC0010.jpg'
    shutil.copyfile(source, inputs/'UPLOAD.jpg')
    with Image.open(source) as image:
        image.save(tmp_path/'source.png')
    write_description_table(tmp_path/'description.csv', DESCRIPTION, {})
    command = [sys.executable, '-m', 'src.imageCompositeConverter', str(inputs),
               '--descriptions-path', str(tmp_path/'description.csv'), '--output-dir', str(tmp_path/'output'),
               '--start', 'UPLOAD', '--end', 'UPLOAD', '--execution-mode', 'semantic-only',
               '--search-seconds', '60', '--search-max-seconds', '120', '--search-seed', str(seed),
               '--log-file', str(tmp_path/'converter.local.log'), '--fail-on-batch-failures']
    completed = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=45)
    assert completed.returncode == 0, completed.stdout.decode(errors='replace')
    job = {}
    collect_result(tmp_path, job, completed.returncode)
    assert job['quality'] == 'passed' and job['pixel_quality']['passed']
    assert job['search_summary']['satisfactory']
    assert job['search_summary']['candidate_evaluations'] > 0
