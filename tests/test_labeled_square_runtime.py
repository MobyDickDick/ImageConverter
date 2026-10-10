from pathlib import Path
import copy
import json

import cv2
import fitz
import numpy as np
import pytest

from src.iCCModules import imageCompositeConverterGeometryIr as geometry
from src.iCCModules import imageCompositeConverterNonCompositeRuntime as runtime
from src.iCCModules.imageCompositeConverterLabeledSquare import fit_labeled_square
from src.iCCModules.imageCompositeConverterRendering import render_svg_to_numpy_inprocess
from tools.evaluate_labeled_square_recheck import labeled_square_semantics, measure
from tools.review_conversion_quality import normalized_mse

ROOT = Path(__file__).resolve().parents[1]
DESCRIPTION = 'Kelle mit Quadrat oben, mittigem Griff nach unten und Text "P" im Quadrat.'


def render(svg, width, height):
    return render_svg_to_numpy_inprocess(svg, width, height, fitz_module=fitz, np_module=np, cv2_module=cv2)


def fit(image, description=DESCRIPTION, error_fn=None):
    height, width = image.shape[:2]
    return fit_labeled_square(geometry.buildGeometryIrFromDescriptionImpl(description), image=image,
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
    assert params['labeled_square_registration']['source'] == 'raster_labeled_square_registration_v1'
    return artifacts[-1]


@pytest.mark.parametrize('name', ['AC0731_1_L', 'AC0731_1_M', 'AC0731_1_S', 'AC0731_L', 'AC0731_M', 'AC0731_S'])
def test_runtime_registers_all_color_and_size_holdouts_without_samples(name, monkeypatch):
    image = cv2.imread(str(ROOT/f'artifacts/images_to_convert/{name}.jpg'))
    svg, raster = convert(image, 'anonymous_square', monkeypatch)
    assert labeled_square_semantics(svg) == 1.
    assert normalized_mse(image, raster)[1] < .006


def test_runtime_is_invariant_to_filename_and_preserves_quoted_case(monkeypatch):
    image = cv2.imread(str(ROOT/'artifacts/images_to_convert/AC0731_1_L.jpg'))
    svg, raster = convert(image, 'AC0731_1_L', monkeypatch)
    renamed_svg, renamed_raster = convert(image, 'unrelated_holdout', monkeypatch)
    assert svg == renamed_svg and '>P</text>' in svg
    np.testing.assert_array_equal(raster, renamed_raster)


@pytest.mark.parametrize('label', ['P', 'M', 'T', 'p', 'rF'])
def test_parser_preserves_explicit_labels_without_imposing_one(label):
    ir = geometry.buildGeometryIrFromDescriptionImpl(DESCRIPTION.replace('"P"', f'"{label}"'))
    assert ir[0]['label'] == label
    assert f'>{label}</text>' in geometry.renderGeometryIrToSvgImpl(25, 45, ir)
    plain = geometry.buildGeometryIrFromDescriptionImpl('Kelle mit Quadrat oben, ohne Text "P".')
    assert 'label' not in plain[0]
    assert '<text' not in geometry.renderGeometryIrToSvgImpl(25, 45, plain)


def synthetic(scale=1, fill='#2458a0', label='P', shift=0, shape='square', stem=True):
    width, height = 52*scale, 64*scale
    x, y, side = 6+shift, 8, 30
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">'
           + (f'<path d="M {(x+side/2)*scale} {(y+side)*scale} L {(x+side/2)*scale} {58*scale}" '
              f'stroke="#747474" stroke-width="{2*scale}"/>' if stem else '')
           + (f'<rect x="{x*scale}" y="{y*scale}" width="{side*scale}" height="{side*scale}" '
              f'fill="{fill}" stroke="#aaa090" stroke-width="{1.5*scale}"/>' if shape == 'square' else
              f'<circle cx="{(x+side/2)*scale}" cy="{(y+side/2)*scale}" r="{side*scale/2}" fill="{fill}"/>')
           + (f'<text x="{(x+side/2)*scale}" y="{(y+side*.73)*scale}" font-size="{side*.6*scale}" '
              f'font-weight="600" font-family="Arial, Helvetica, sans-serif" text-anchor="middle" fill="#f3e9d7">{label}</text>' if label else '')
           + '</svg>')
    return svg, render(svg, width, height)


@pytest.mark.parametrize('scale', [1, 2])
@pytest.mark.parametrize('fill', ['#2458a0', '#a05020'])
@pytest.mark.parametrize('label', ['P', 'M', 'T'])
@pytest.mark.parametrize('shift', [0, 8])
def test_registration_generalizes_position_scale_color_and_described_glyph(scale, fill, label, shift):
    _, image = synthetic(scale, fill, label, shift)
    result = fit(image, DESCRIPTION.replace('"P"', f'"{label}"'))
    assert result is not None
    assert result['final_error'] < result['initial_error']
    assert result['geometry_ir'][0]['label'] == label
    assert result['evaluations'] <= 204
    assert normalized_mse(image, result['rendered'])[1] < .006


@pytest.mark.parametrize('kwargs', [{'label': ''}, {'stem': False}, {'shape': 'circle'}])
def test_detector_rejects_missing_required_parts_and_wrong_body_shape(kwargs):
    _, image = synthetic(**kwargs)
    assert fit(image) is None


def test_constant_error_cannot_overwrite_geometry_or_mutate_input():
    _, image = synthetic()
    ir = geometry.buildGeometryIrFromDescriptionImpl(DESCRIPTION)
    original = copy.deepcopy(ir)
    assert fit_labeled_square(ir, image=image, render_fn=lambda candidate: image, error_fn=lambda raster: 1.) is None
    assert ir == original
    assert fit(image, 'Kelle mit Quadrat oben, ohne Text.') is None


def test_metrics_calibrate_to_perfect_saved_svg_and_reject_semantic_mutations(tmp_path):
    source, image = synthetic()
    image_path, svg_path = tmp_path/'perfect.png', tmp_path/'perfect.svg'
    assert cv2.imwrite(str(image_path), image)
    svg_path.write_text(source, encoding='utf-8')
    record = measure(image_path, svg_path)
    assert record['mean_delta2'] == 0.
    assert record['metrics'] == {'error_per_pixel': 0., 'edge_alignment': 1., 'object_mask_iou': 1.,
                                 'semantic_score': 1., 'dimension_match': 1.}
    assert labeled_square_semantics(source.replace('>P</text>', '>T</text>')) == 0.
    assert labeled_square_semantics(source.replace('M 21.0 38', 'M 21.0 42')) == 0.
    assert labeled_square_semantics(source.replace('</svg>', '<circle r="2"/></svg>')) == 0.
    assert labeled_square_semantics(source.replace('width="30"', 'width="50"')) == 0.


def test_runner_rejects_stale_cli_outputs(tmp_path, monkeypatch):
    import sys
    from tools.run_labeled_square_recheck import main
    manifest = tmp_path/'manifest.json'
    manifest.write_text('{}', encoding='utf-8')
    output = tmp_path/'used'
    (output/'before').mkdir(parents=True)
    monkeypatch.setattr(sys, 'argv', ['recheck', str(manifest), '--output-dir', str(output)])
    with pytest.raises(ValueError, match='fresh output directory'):
        main()


def test_frozen_cli_evidence_passes_both_gates():
    from tools.evaluate_labeled_square_recheck import evaluate
    root = ROOT/'artifacts/evaluation/labeled_square_recheck_v1'
    manifest = json.loads((root/'manifest.json').read_text(encoding='utf-8'))
    report = evaluate(manifest, root)
    assert report['satisfaction_gate']['summary']['satisfactory'] == 6
    assert all(not c['regressed_metrics'] for c in report['satisfaction_gate']['cases'])
