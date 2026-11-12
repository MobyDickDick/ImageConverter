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
FREE_DESCRIPTION = ('Es ist ein liegendes Rechteck mit einer grauen Umrandung. '
                    'Es gibt einen vertikalen Graustufenübergang (Farbübergang). '
                    'Die maximale Helligkeit ist ca. 1/3 unter dem oberen Bildrand. '
                    'Das dunkelste Grau dieses Farbübergang ist immer noch leicht heller als der Rand.')


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


@pytest.mark.parametrize('word', ['Graustufenübergang', 'Graustufenverlauf', 'Farbübergang', 'Farbverlauf'])
def test_free_gradient_description_and_whole_motif_variation(word):
    description = FREE_DESCRIPTION.replace('Graustufenübergang', word)
    description += ' Die gesamte Darstellung ist ein wenig größer dargestellt und etwas nach links und unten versetzt.'
    contract = panel_contract(description)
    assert contract and contract['axis'] == 1 and contract['upper']
    image, _ = synthetic(1, 1)
    result = fit(image, description)
    assert result is not None and result['profile_quality']['passed']
    root = ET.fromstring(result['svg'])
    assert len(root.findall('{*}rect')) == 1 and len(root.findall('.//{*}stop')) == 4


@pytest.mark.parametrize('extra', [' Ein Kreis.', ' Eine diagonale Linie.', ' Ein Pfeil.',
                                 ' Ein horizontaler Farbverlauf.', ' Ein Text im Rechteck.'])
def test_free_gradient_contract_does_not_suppress_extra_objects_or_axes(extra):
    assert panel_contract(FREE_DESCRIPTION+extra) is None


def test_free_gradient_peak_polarity_is_checked_on_raster():
    image, _ = synthetic(1, 1)
    assert fit(image[::-1].copy(), FREE_DESCRIPTION) is None
    assert fit(image, FREE_DESCRIPTION.replace('oberen Bildrand', 'unteren Bildrand')) is None


def test_shared_normalization_preserves_the_only_greyscale_cue():
    from src.iCCModules.imageCompositeConverterDescriptionLanguage import normalize_description
    description = ('Ein Rechteck mit dunkler Umrandung. Es gibt einen vertikalen '
                   'Graustufenübergang. Das hellste Band liegt im Inneren.')
    assert panel_contract(description) is not None
    assert panel_contract(normalize_description(description)) == panel_contract(description)


def test_complete_gradient_prose_is_not_bypassed_by_insufficient_shape_dispatch():
    from src.iCCModules.imageCompositeConverterNonCompositeRuntime import runNonCompositeIterationImpl
    description = FREE_DESCRIPTION.split('Es gibt', 1)[1]
    description = 'Es gibt'+description
    image, _ = synthetic(1, 1)
    w, h = image.shape[1], image.shape[0]
    saved, logs = [], []
    params = {'mode': 'insufficient_description'}
    result = runNonCompositeIterationImpl(mode='insufficient_description', params=params,
        stripe_strategy=None, semantic_mode_visual_override=False, width=w, height=h,
        base_name='unrelated', description=description, perc_img=image, img_path='unrelated.png',
        print_fn=lambda *args: None, render_embedded_raster_svg_fn=lambda *args: None,
        build_gradient_stripe_svg_fn=lambda *args, **kwargs: None,
        build_gradient_stripe_validation_log_lines_fn=lambda **kwargs: [],
        write_validation_log_fn=logs.append, render_svg_to_numpy_fn=render,
        record_render_failure_fn=lambda *args, **kwargs: None,
        write_attempt_artifacts_fn=lambda svg, raster: saved.append(svg),
        calculate_error_fn=lambda a, b: float(np.mean((a.astype(float)-b)**2)))
    assert result is not None and 'framed_panel_registration' in params
    assert logs[-1] == ['status=non_composite_raster_framed_panel']
    assert len(ET.fromstring(saved[-1]).findall('{*}rect')) == 1


@pytest.mark.parametrize('axis', [0, 1])
def test_clipped_frame_is_not_fitted_as_an_extra_paint_transition(axis):
    from src.iCCModules.imageCompositeConverterSearchPortfolio import search_configuration, configured_image_search
    from tools.run_plan_b_variations import measure_quality
    w, h = (92, 46) if axis else (46, 92)
    x, y, rw, rh = (-1.2, 2.1, 89.4, 45.2) if axis else (2.1, -1.2, 45.2, 89.4)
    coords = 'x1="0" x2="0" y1="2.1" y2="47.3"' if axis else 'y1="0" y2="0" x1="2.1" x2="47.3"'
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}">'
           f'<defs><linearGradient id="independent" gradientUnits="userSpaceOnUse" {coords}>'
           '<stop offset="0" stop-color="#a7a7a7"/><stop offset=".26" stop-color="#ededed"/>'
           '<stop offset=".41" stop-color="#f1f1f1"/><stop offset="1" stop-color="#b3b3b3"/>'
           f'</linearGradient></defs><rect x="{x}" y="{y}" width="{rw}" height="{rh}" '
           'fill="url(#independent)" stroke="#858585" stroke-width="1.4"/></svg>')
    description = (f'Ein Rechteck mit grauem Rand und {"vertikalem" if axis else "horizontalem"} '
                   'Graustufenübergang. Das hellste Band liegt im Inneren.')
    image = render(svg, w, h)
    with search_configuration(mode='portfolio', adaptive=True, seed=816327,
                              seconds=20, max_seconds=20, minimum_seconds=20):
        with configured_image_search('unrelated-clipped-panel'):
            result = fit(image, description)
    assert result is not None and result['profile_quality']['passed']
    assert measure_quality(image, result['svg'])['satisfactory']


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
