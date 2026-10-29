from pathlib import Path
from xml.etree import ElementTree as ET

import cv2
import numpy as np
import pytest

from src.iCCModules.imageCompositeConverterAdaptiveSearch import ImageSearch, SearchPolicy, image_search, pixel_quality
from src.iCCModules.imageCompositeConverterPairedLinePanel import fit_paired_line_panel
from tools.run_plan_b_variations import render


ROOT = Path(__file__).resolve().parents[1]
DESCRIPTION = ('Es ist ein graues Rechteck. Es gibt zwei schräge Linien welche bezüglich der '
               'horizontalen Mittellinie der symmetrisch ist. Es gibt eine Abstufung der Grauwerte. '
               'In der horizontalen Mittellinie ist der Farrbwert ein wenig dunkler oben und '
               'unterhalb ein wenig heller. Auf der rechten Seite gibt es zwei kurze horizontale graue Striche.')


def fit(image, description=DESCRIPTION, render_fn=render, error_fn=None):
    return fit_paired_line_panel(image.shape[1], image.shape[0], description=description, image=image,
        render_fn=render_fn, error_fn=error_fn or (lambda a, b: float(np.mean((a.astype(float)-b)**2))))


def synthetic(scale=1, missing=False):
    w, h = 60*scale, 30*scale
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 60 30">'
           '<defs><linearGradient id="paint" x1="0" x2="0" y1="0" y2="1">'
           '<stop offset="0" stop-color="#bfbfbf"/><stop offset=".4" stop-color="#f8f8f8"/>'
           '<stop offset=".5" stop-color="#e7e7e7"/><stop offset=".6" stop-color="#f8f8f8"/>'
           '<stop offset="1" stop-color="#bfbfbf"/></linearGradient></defs>'
           '<rect x=".5" y=".5" width="59" height="29" fill="url(#paint)" stroke="#999999"/>'
           '<path d="M 0 9 L 60 3 M 0 21 L 60 27" stroke="#999999" fill="none"/>'
           '<path d="M 39 13 H 51" stroke="#999999"/>'
           + ('' if missing else '<path d="M 39 17 H 51" stroke="#999999"/>')+'</svg>')
    return render(svg, w, h)


def test_actual_jpeg_keeps_all_four_marks_and_uses_search_budget():
    image = cv2.imread(str(ROOT/'artifacts/images_to_convert/AC0VR2_AB_M.jpg'))
    session = ImageSearch(SearchPolicy(seconds=120, max_seconds=240))
    with image_search(session):
        result = fit(image)
    assert result is not None and session.evaluations > 0
    assert pixel_quality(image, result['rendered'])['passed']
    root = ET.fromstring(result['svg'])
    assert len(root.findall('{*}polyline')) == 2 and len(root.findall('{*}path')) == 2
    assert len(root.findall('.//{*}stop')) <= 9 and not root.findall('.//{*}image')
    assert np.max(result['rendered'][12, 42:52]) < 205
    assert np.max(result['rendered'][16, 42:52]) < 205


@pytest.mark.parametrize('scale', [1, 2, 3])
def test_independent_native_panels_at_other_resolutions(scale):
    image = synthetic(scale)
    result = fit(image)
    assert result is not None and pixel_quality(image, result['rendered'])['passed']


@pytest.mark.parametrize('damage', ['missing_bar', 'extra_object', 'asymmetric', 'color'])
def test_unsupported_raster_is_rejected(damage):
    image = synthetic(missing=damage == 'missing_bar')
    if damage == 'extra_object':
        image[13:17, 20:24] = 40
    elif damage == 'asymmetric':
        image[20:28, 1:59] = 240
    elif damage == 'color':
        image[:, :, 0] = 10
    assert fit(image) is None


def test_description_failed_render_and_nonfinite_error_are_guards():
    image = synthetic()
    assert fit(image, DESCRIPTION+' Zusätzlich ein Kreis.') is None
    assert fit(image, render_fn=lambda *args: None) is None
    assert fit(image, error_fn=lambda *args: float('nan')) is None


def test_expired_budget_does_not_render():
    image = synthetic()
    session = ImageSearch(SearchPolicy(seconds=1, max_seconds=1), clock=lambda: 2.)
    session.spent = 2.
    with image_search(session):
        assert fit(image, render_fn=lambda *args: pytest.fail('expired budget')) is None


def test_catalogs_supply_matching_geometry_instead_of_manual_review():
    from src.imageConverterGui import catalog_descriptions
    from src.iCCModules.imageCompositeConverterDescriptions import loadDescriptionMappingImpl
    from src.iCCModules.imageCompositeConverterNaming import getBaseNameFromFileImpl
    from src.iCCModules.imageCompositeConverterPairedLinePanel import paired_line_contract
    for folder in ('images_to_convert', 'descriptions'):
        mapping = loadDescriptionMappingImpl(str(ROOT/'artifacts'/folder/'Finale_Wurzelformen_V3.xml'),
                                            get_base_name_from_file_fn=getBaseNameFromFileImpl)
        assert paired_line_contract(mapping['AC0VR2_AB_M'])
    assert paired_line_contract(catalog_descriptions()['AC0VR2_AB_M'])


@pytest.mark.parametrize('seed', [273, 1947])
def test_gui_cli_upload_with_user_description_passes_saved_result_check(tmp_path, seed):
    import shutil
    import subprocess
    import sys
    from PIL import Image
    from src.imageConverterGui import collect_result, write_description_table

    inputs = tmp_path/'input'
    inputs.mkdir()
    # No catalog identity or sample is available under this neutral upload name.
    source = ROOT/'artifacts/images_to_convert/AC0VR2_AB_M.jpg'
    shutil.copyfile(source, inputs/'UPLOAD.jpg')
    with Image.open(source) as image:
        image.save(tmp_path/'source.png')
    write_description_table(tmp_path/'description.csv', DESCRIPTION, {})
    command = [sys.executable, '-m', 'src.imageCompositeConverter', str(inputs),
               '--descriptions-path', str(tmp_path/'description.csv'), '--output-dir', str(tmp_path/'output'),
               '--start', 'UPLOAD', '--end', 'UPLOAD', '--execution-mode', 'semantic-only',
               '--search-seconds', '120', '--search-max-seconds', '240', '--search-seed', str(seed),
               '--log-file', str(tmp_path/'converter.local.log'), '--fail-on-batch-failures']
    completed = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=40)
    assert completed.returncode == 0, completed.stdout.decode(errors='replace')
    job = {}
    collect_result(tmp_path, job, completed.returncode)
    assert job['quality'] == 'passed' and job['pixel_quality']['passed']
    assert job['search_summary']['satisfactory']
    assert job['search_summary']['candidate_evaluations'] > 0
