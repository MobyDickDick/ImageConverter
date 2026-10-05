from pathlib import Path
import copy
import json

import cv2
import fitz
import numpy as np
import pytest

from src.iCCModules import imageCompositeConverterGeometryIr as geometry
from src.iCCModules import imageCompositeConverterNonCompositeRuntime as runtime
from src.iCCModules.imageCompositeConverterCheckmark import fit_checkmark_disk
from src.iCCModules.imageCompositeConverterRendering import render_svg_to_numpy_inprocess
from tools.evaluate_checkmark_disk_recheck import checkmark_disk_semantics, measure
from tools.review_conversion_quality import normalized_mse

ROOT = Path(__file__).resolve().parents[1]
DESCRIPTION = 'Grüner Haken aus zwei schrägen Liniensegmenten vor einer grauen Kreisscheibe mit radialem Helligkeitsverlauf und grauem Rand. Weißer Hintergrund.'


def render(svg, width, height):
    return render_svg_to_numpy_inprocess(svg, width, height, fitz_module=fitz, np_module=np, cv2_module=cv2)


def fit(image, description=DESCRIPTION, error_fn=None):
    height, width = image.shape[:2]
    return fit_checkmark_disk(geometry.buildGeometryIrFromDescriptionImpl(description), image=image,
        render_fn=lambda ir: render(geometry.renderGeometryIrToSvgImpl(width, height, ir), width, height),
        error_fn=error_fn or (lambda raster: normalized_mse(image, raster)[0]))


def convert(image, name, monkeypatch):
    artifacts, logs = [], []
    height, width = image.shape[:2]
    monkeypatch.setattr(runtime, '_try_load_sample_svg', lambda **kwargs: pytest.fail('must not read sample SVGs'))
    params = {'mode': 'non_composite', 'description_fragments': [{'text': DESCRIPTION}]}
    result = runtime.runNonCompositeIterationImpl(
        mode='non_composite', params=params, stripe_strategy=None,
        semantic_mode_visual_override=False, width=width, height=height, base_name=name,
        description=DESCRIPTION.lower(), perc_img=image, img_path=f'{name}.jpg', print_fn=lambda *args: None,
        render_embedded_raster_svg_fn=lambda path: pytest.fail('must not embed raster'),
        build_gradient_stripe_svg_fn=lambda *args, **kwargs: None,
        build_gradient_stripe_validation_log_lines_fn=lambda **kwargs: [],
        write_validation_log_fn=logs.append, render_svg_to_numpy_fn=render,
        record_render_failure_fn=lambda *args, **kwargs: None,
        write_attempt_artifacts_fn=lambda svg, raster: artifacts.append((svg, raster)),
        calculate_error_fn=lambda target, raster: normalized_mse(target, raster)[0],
    )
    assert result is not None
    assert 'non_composite_selection=semantic_description_geometry' in logs[-1]
    assert params['checkmark_disk_registration']['source'] == 'raster_checkmark_disk_registration_v1'
    return artifacts[-1]


@pytest.mark.parametrize('name', ['GE1003_M', 'GE1003_L', 'GE1003_S'])
def test_runtime_registers_size_holdouts_without_reference_vectors(name, monkeypatch):
    image = cv2.imread(str(ROOT/f'artifacts/images_to_convert/{name}.jpg'))
    svg, raster = convert(image, 'anonymous_checkmark', monkeypatch)
    assert checkmark_disk_semantics(svg) == 1.
    assert normalized_mse(image, raster)[1] < .004


def test_runtime_filename_invariance(monkeypatch):
    image = cv2.imread(str(ROOT/'artifacts/images_to_convert/GE1003_M.jpg'))
    first, a = convert(image, 'GE1003_M', monkeypatch)
    second, b = convert(image, 'independent_holdout', monkeypatch)
    assert first == second
    np.testing.assert_array_equal(a, b)


def synthetic(scale=1, shift=0, color='#188c35', mark=True, disk=True):
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{60*scale}" height="{60*scale}">'
           '<defs><radialGradient id="disk"><stop offset="0%" stop-color="#dddddd"/>'
           '<stop offset="70%" stop-color="#bbbbbb"/><stop offset="100%" stop-color="#909090"/>'
           '</radialGradient></defs><rect width="100%" height="100%" fill="#ffffff"/>'
           + (f'<ellipse cx="{(23+shift)*scale}" cy="{39*scale}" rx="{15*scale}" ry="{15*scale}" '
              f'fill="url(#disk)" stroke="#888888" stroke-width="{scale}"/>' if disk else '')
           + (f'<path d="M {(6+shift)*scale} {24*scale} L {(20+shift)*scale} {40*scale} L {(48+shift)*scale} {8*scale}" '
              f'stroke="{color}" stroke-width="{6*scale}" fill="none" stroke-linecap="round" stroke-linejoin="round"/>' if mark else '')
           + '</svg>')
    return svg, render(svg, 60*scale, 60*scale)


@pytest.mark.parametrize('scale', [1, 2])
@pytest.mark.parametrize('shift', [0, 5])
@pytest.mark.parametrize('color', ['#188c35', '#24742d'])
def test_registration_generalizes_geometry_and_green_shades(scale, shift, color):
    _, image = synthetic(scale, shift, color)
    result = fit(image)
    assert result is not None
    assert result['final_error'] < result['initial_error']
    assert normalized_mse(image, result['rendered'])[1] < .006
    svg = geometry.renderGeometryIrToSvgImpl(60*scale, 60*scale, result['geometry_ir'])
    assert checkmark_disk_semantics(svg) == 1.
    assert svg.count('<ellipse') == 1 and '<image' not in svg
    assert '<radialGradient' in svg
    assert result['evaluations'] <= 169


@pytest.mark.parametrize('mark,disk', [(False,True), (True,False), (False,False)])
def test_missing_evidence_does_not_invent_primitives(mark, disk):
    _, image = synthetic(mark=mark, disk=disk)
    assert fit(image) is None


def test_constant_and_nonfinite_errors_do_not_accept_or_mutate_input():
    _, image = synthetic()
    ir = geometry.buildGeometryIrFromDescriptionImpl(DESCRIPTION)
    original = copy.deepcopy(ir)
    for error in (42., float('nan'), float('inf')):
        result = fit_checkmark_disk(ir, image=image, render_fn=lambda candidate: render(
            geometry.renderGeometryIrToSvgImpl(60, 60, candidate),60,60), error_fn=lambda r: error)
        assert result is None and ir == original


def test_existing_plain_checkmark_and_checkbox_do_not_gain_disks():
    for description in ('Grüner Haken aus zwei schrägen Liniensegmenten.', 'Checkbox mit grünem Haken.'):
        ir = geometry.buildGeometryIrFromDescriptionImpl(description)
        assert not any(e.get('role') == 'checkmark_disk' for e in ir)
        assert fit_checkmark_disk(ir, image=np.zeros((30,30,3)), render_fn=None, error_fn=None) is None


def test_saved_cli_evidence_passes_unchanged_gates():
    from tools.evaluate_checkmark_disk_recheck import evaluate
    evidence = ROOT/'artifacts/evaluation/checkmark_disk_recheck_v1'
    manifest = json.loads((evidence/'manifest.json').read_text(encoding='utf-8'))
    report = evaluate(manifest,evidence)
    assert report == json.loads((evidence/'report_2026-10-05.json').read_text(encoding='utf-8'))
    assert all(c['satisfactory'] and not c['regressed_metrics'] for c in report['satisfaction_gate']['cases'])


def test_semantics_rejects_wrong_color_geometry_layers_and_extra_primitives():
    image = cv2.imread(str(ROOT/'artifacts/images_to_convert/GE1003_M.jpg'))
    ir = fit(image)['geometry_ir']
    good = geometry.renderGeometryIrToSvgImpl(25,25,ir)
    assert checkmark_disk_semantics(good) == 1.
    for mutation in ('red','no_disk','layers','straight','extra','detached'):
        bad = copy.deepcopy(ir)
        if mutation == 'red': bad[3]['stroke'] = '#c02020'
        if mutation == 'no_disk': bad.pop(1)
        if mutation == 'layers': bad[1],bad[3] = bad[3],bad[1]
        if mutation == 'straight': bad[3]['points'][1][1] = .2
        if mutation == 'extra': bad.append(copy.deepcopy(bad[1]))
        if mutation == 'detached': bad[1]['bbox'][0] = .8
        assert checkmark_disk_semantics(geometry.renderGeometryIrToSvgImpl(25,25,bad)) == 0.


def test_measurement_is_calibrated_on_identical_raster_and_svg(tmp_path):
    svg, image = synthetic()
    image_path, svg_path = tmp_path/'source.png', tmp_path/'vector.svg'
    cv2.imwrite(str(image_path), image)
    svg_path.write_text(svg,encoding='utf-8')
    record = measure(image_path,svg_path)
    assert record['mean_delta2'] == 0 and record['metrics']['error_per_pixel'] == 0
    assert record['metrics']['edge_alignment'] == 1 and record['metrics']['object_mask_iou'] == 1
    assert record['metrics']['dimension_match'] == 1


