from pathlib import Path

import cv2
import fitz
import numpy as np
import pytest

from src.iCCModules import imageCompositeConverterGeometryIr as geometry
from src.iCCModules import imageCompositeConverterNonCompositeRuntime as runtime
from src.iCCModules.imageCompositeConverterPump import fit_pump_geometry
from src.iCCModules.imageCompositeConverterRendering import render_svg_to_numpy_inprocess
from tools.evaluate_pump_recheck import circle_triangle_semantics, measure
from tools.review_conversion_quality import normalized_mse

ROOT = Path(__file__).resolve().parents[1]
DESCRIPTION = 'Pumpensymbol: Kreis mit einem gefüllten Dreieck, dessen Spitze nach rechts zeigt.'


def render(svg, width, height):
    return render_svg_to_numpy_inprocess(svg, width, height, fitz_module=fitz, np_module=np, cv2_module=cv2)


def convert(image, name, monkeypatch):
    artifacts, logs = [], []
    height, width = image.shape[:2]
    monkeypatch.setattr(runtime, '_try_load_sample_svg', lambda **kwargs: pytest.fail('must not read sample SVGs'))
    params = {'mode': 'non_composite'}
    result = runtime.runNonCompositeIterationImpl(
        mode='non_composite', params=params, stripe_strategy=None,
        semantic_mode_visual_override=False, width=width, height=height, base_name=name,
        description=DESCRIPTION, perc_img=image, img_path=f'{name}.jpg', print_fn=lambda *args: None,
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
    assert params['pump_registration']['source'] == 'raster_circle_triangle_v1'
    return artifacts[-1]


@pytest.mark.parametrize('name', ['AC0252_1', 'AC0252_2', 'AC0252'])
def test_runtime_recovers_circle_triangle_for_unseen_color_variants(name, monkeypatch):
    image = cv2.imread(str(ROOT/f'artifacts/images_to_convert/{name}.jpg'))
    svg, raster = convert(image, 'anonymous_pump', monkeypatch)
    assert circle_triangle_semantics(svg) == 1.
    assert normalized_mse(image, raster)[1] < .003


def test_runtime_is_invariant_to_filename(monkeypatch):
    image = cv2.imread(str(ROOT/'artifacts/images_to_convert/AC0252_1.jpg'))
    svg, raster = convert(image, 'AC0252_1', monkeypatch)
    renamed_svg, renamed_raster = convert(image, 'unrelated_holdout', monkeypatch)
    assert svg == renamed_svg
    np.testing.assert_array_equal(raster, renamed_raster)


def synthetic(scale=1, direction='rechts', shape='triangle', fill='#2458a0'):
    width, height = 66*scale, 50*scale
    vertices = np.array([[.8, 0], [-.5, -.7], [-.5, .7]])
    turns = {'rechts': 0, 'unten': 1, 'links': 2, 'oben': 3}[direction]
    for _ in range(turns):
        vertices = np.column_stack((-vertices[:,1], vertices[:,0]))
    vertices = (vertices*17+[25,26])*scale
    point_text = ' '.join(f'{x},{y}' for x,y in vertices)
    objects = {
        'triangle': f'<polygon points="{point_text}" fill="#f4e6cc"/>',
        'rectangle': f'<rect x="{16*scale}" y="{19*scale}" width="{16*scale}" height="{14*scale}" fill="#f4e6cc"/>',
        'dot': f'<circle cx="{25*scale}" cy="{26*scale}" r="{8*scale}" fill="#f4e6cc"/>',
        'none': '',
    }
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">'
           f'<ellipse cx="{25*scale}" cy="{26*scale}" rx="{17*scale}" ry="{17*scale}" '
           f'fill="{fill}" stroke="#707070" stroke-width="{1.2*scale}"/>{objects[shape]}</svg>')
    return svg, render(svg, width, height)


def fit(image, description=DESCRIPTION):
    height, width = image.shape[:2]
    return fit_pump_geometry(geometry.buildGeometryIrFromDescriptionImpl(description),
        image=image, description=description,
        render_fn=lambda candidate: render(geometry.renderGeometryIrToSvgImpl(width, height, candidate), width, height),
        error_fn=lambda raster: normalized_mse(image, raster)[0])


@pytest.mark.parametrize('scale', [1, 2])
@pytest.mark.parametrize('direction', ['rechts', 'links', 'oben', 'unten'])
@pytest.mark.parametrize('fill', ['#2458a0', '#b35020'])
def test_observation_generalizes_color_position_scale_and_orientation(scale, direction, fill):
    _, image = synthetic(scale, direction, fill=fill)
    result = fit(image, DESCRIPTION.replace('rechts', direction))
    assert result is not None
    assert result['final_error'] < result['initial_error']
    assert normalized_mse(image, result['rendered'])[1] < .002
    circle, triangle = result['geometry_ir']
    assert circle['fill'] != '#e42a4f'
    assert triangle['fill'] != '#e7e7e7'


@pytest.mark.parametrize('shape', ['none', 'rectangle', 'dot'])
def test_detector_rejects_other_interior_topologies(shape):
    _, image = synthetic(shape=shape)
    assert fit(image) is None


def test_direction_and_extra_described_objects_are_hard_constraints():
    _, image = synthetic()
    assert fit(image, DESCRIPTION.replace('rechts', 'links')) is None
    assert fit(image, DESCRIPTION+' Mit Text.') is None
    assert fit(image, DESCRIPTION+' Mit Griff links.') is None


def test_unconfirmed_pump_seed_does_not_override_existing_selection():
    ir = geometry.buildGeometryIrFromDescriptionImpl(DESCRIPTION+' Mit Griff links.')
    assert not runtime._prefer_semantic_description_geometry(ir)
    _, image = synthetic()
    fitted = fit(image)
    assert runtime._prefer_semantic_description_geometry(fitted['geometry_ir'])


def test_quality_metrics_calibrate_to_perfect_saved_svg_and_reject_wrong_topology(tmp_path):
    source, image = synthetic()
    svg_path, image_path = tmp_path/'perfect.svg', tmp_path/'perfect.png'
    svg_path.write_text(source, encoding='utf-8')
    assert cv2.imwrite(str(image_path), image)
    measured = measure(image_path, svg_path)
    assert measured['mean_delta2'] == 0.
    assert measured['metrics'] == {'error_per_pixel': 0., 'edge_alignment': 1., 'object_mask_iou': 1.,
                                   'semantic_score': 1., 'dimension_match': 1.}
    assert circle_triangle_semantics(synthetic(direction='links')[0]) == 0.
    assert circle_triangle_semantics(synthetic(shape='rectangle')[0]) == 0.
    assert circle_triangle_semantics(source.replace('</svg>', '<text>T</text></svg>')) == 0.
    assert circle_triangle_semantics(source.replace('38.6,26.0', '65,26')) == 0.


def test_recheck_runner_rejects_stale_cli_outputs(tmp_path, monkeypatch):
    import sys
    from tools.run_pump_recheck import main
    manifest = tmp_path/'manifest.json'
    manifest.write_text('{}', encoding='utf-8')
    output = tmp_path/'used_output'
    (output/'before').mkdir(parents=True)
    monkeypatch.setattr(sys, 'argv', ['recheck', str(manifest), '--output-dir', str(output)])
    with pytest.raises(ValueError, match='fresh output directory'):
        main()
